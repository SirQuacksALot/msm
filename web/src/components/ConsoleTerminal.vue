<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'



const el = ref<HTMLElement | null>(null)
const connected = ref(false)
const busy = ref(false)
const autoscroll = ref(true)

let term: Terminal | null = null
let fit: FitAddon | null = null
let es: EventSource | null = null
let ro: ResizeObserver | null = null

const props = defineProps<{ id: string; height?: string }>()
// ANSI 32 = "green" → nutzt die `green`-Slot aus dem xterm-Theme (= --color-accent)
const PROMPT = '\x1b[32m> \x1b[0m'
let currentLine = ''
const history: string[] = []
let histIdx = 0

function writeRaw(s: string) {
  term?.write(s, () => {
    if (autoscroll.value) {
      requestAnimationFrame(() => term?.scrollToBottom())
    }
  })
}

function printLine(line: string) {
  // Wenn gerade ein Befehl unterwegs ist, keine Prompt-Zeile stören
  if (busy.value) {
    writeRaw(line + '\r\n')
    return
  }
  // Aktuelle Eingabezeile löschen, Log schreiben, Prompt+Input wiederherstellen
  writeRaw('\r\x1b[K')
  writeRaw(line + '\r\n')
  writeRaw(PROMPT + currentLine)
}

function showPrompt() {
  writeRaw(PROMPT)
}

function rewriteLine() {
  writeRaw('\r\x1b[K')
  writeRaw(PROMPT + currentLine)
}

async function submit() {
  if (busy.value) return
  const cmd = currentLine.trim()
  currentLine = ''
  writeRaw('\r\n')

  if (!cmd) {
    showPrompt()
    return
  }

  history.push(cmd)
  histIdx = history.length

  // Echo der Eingabe, damit sie im Scrollback bleibt
  writeRaw(`${PROMPT}${cmd}\r\n`)

  busy.value = true
  try {
    const r = await fetch(`/api/servers/${props.id}/console/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    })
    const j = await r.json()
    if (!j.ok) {
      writeRaw(`\x1b[31m[fehler]\x1b[0m ${j.error || 'unbekannt'}\r\n`)
    } else if (j.output) {
      writeRaw(j.output)
      if (!j.output.endsWith('\n')) writeRaw('\r\n')
    }
  } catch (e: any) {
    writeRaw(`\x1b[31m[fehler]\x1b[0m ${e.message}\r\n`)
  } finally {
    busy.value = false
    showPrompt()
  }
}

function onData(data: string) {
  if (busy.value) return

  // Enter
  if (data === '\r') {
    submit()
    return
  }
  // Ctrl+C – Zeile verwerfen
  if (data === '\x03') {
    writeRaw('^C\r\n')
    currentLine = ''
    showPrompt()
    return
  }
  // Backspace
  if (data === '\x7f') {
    if (currentLine.length > 0) {
      currentLine = currentLine.slice(0, -1)
      writeRaw('\b \b')
    }
    return
  }
  // Pfeil hoch – History rückwärts
  if (data === '\x1b[A') {
    if (histIdx > 0) {
      histIdx--
      currentLine = history[histIdx] || ''
      rewriteLine()
    }
    return
  }
  // Pfeil runter – History vorwärts
  if (data === '\x1b[B') {
    if (histIdx < history.length - 1) {
      histIdx++
      currentLine = history[histIdx] || ''
    } else {
      histIdx = history.length
      currentLine = ''
    }
    rewriteLine()
    return
  }
  // Einzelnes druckbares Zeichen
  if (data.length === 1 && data >= ' ' && data !== '\x7f') {
    currentLine += data
    writeRaw(data)
    return
  }
  // Paste (mehrere Zeichen) – nur druckbare filtern
  if (data.length > 1) {
    const printable = data.replace(/[^\x20-\x7e]/g, '')
    if (printable) {
      currentLine += printable
      writeRaw(printable)
    }
  }
}

onMounted(() => {
  if (!el.value) return

  const cv = (n: string) =>
    getComputedStyle(document.documentElement).getPropertyValue(n).trim()

  term = new Terminal({
    theme: {
      background:          cv('--color-console'),
      foreground:          cv('--color-fg'),
      cursor:              cv('--color-accent'),
      selectionBackground: 'rgba(87,199,133,.3)',

      /* ANSI-Slots – Semantik an Tokens gekoppelt */
      red:   cv('--color-danger'),
      green: cv('--color-accent'),
      yellow: cv('--color-warning'),
      blue:  cv('--color-info'),

      /* Slots ohne direkte Entsprechung – bleiben hartkodiert */
      black:   '#1a2029',
      magenta: '#c78ae6',
      cyan:    '#5fd7d7',
      white:   '#d5dde3',
    },
    fontSize: 13,
    fontFamily: 'ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace',
    cursorBlink: true,
    scrollback: 5000,
    convertEol: true,
  })
  fit = new FitAddon()
  term.loadAddon(fit)
  term.open(el.value)
  fit.fit()

  ro = new ResizeObserver(() => fit?.fit())
  ro.observe(el.value)

  term.onData(onData)
  term.focus()

  writeRaw('\x1b[2mServer-Konsole – Befehle eingeben, Enter zum Senden, ↑/↓ für History.\x1b[0m\r\n')
  showPrompt()

  es = new EventSource(`/api/servers/${props.id}/console/stream`)
  es.onopen = () => {
    connected.value = true
    printLine('\x1b[2m[stream verbunden]\x1b[0m')
  }
  es.onerror = () => {
    connected.value = false
    printLine('\x1b[2m[stream getrennt – Server evtl. gestoppt]\x1b[0m')
  }
  es.onmessage = (e) => printLine(e.data)
})

onUnmounted(() => {
  ro?.disconnect()
  es?.close()
  term?.dispose()
})

function clear() {
  term?.clear()
  showPrompt()
}

function focus() {
  term?.focus()
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between text-xs">
      <div class="flex items-center gap-4">
        <span
          :class="connected ? 'text-accent' : 'text-danger'"
          class="flex items-center gap-1.5"
        >
          <span
            :class="connected ? 'bg-accent animate-pulse' : 'bg-danger'"
            class="w-1.5 h-1.5 rounded-full inline-block"
          ></span>
          {{ connected ? 'live' : 'getrennt' }}
        </span>
        <label class="flex items-center gap-1.5 text-muted cursor-pointer select-none">
          <input type="checkbox" v-model="autoscroll" class="accent-accent" />
          Auto-Scroll
        </label>
      </div>
      <button class="text-muted hover:text-muted-hover transition-colors" @click="clear">
        Clear
      </button>
    </div>

    <div
      class="rounded-lg bg-console p-2 overflow-hidden"
      :style="{ height: height || '400px' }"
    >
      <div
        ref="el"
        class="w-full h-full cursor-text"
        @click="focus"
      ></div>
    </div>
  </div>
</template>