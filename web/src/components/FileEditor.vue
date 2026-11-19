<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { oneDark } from '@codemirror/theme-one-dark'
import { yaml } from '@codemirror/lang-yaml'
import { json } from '@codemirror/lang-json'
import { javascript } from '@codemirror/lang-javascript'
import { markdown } from '@codemirror/lang-markdown'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { xml } from '@codemirror/lang-xml'
import { StreamLanguage } from '@codemirror/language'
import { properties } from '@codemirror/legacy-modes/mode/properties'
import { NModal, NButton, NIcon, NSpin } from 'naive-ui'
import { SaveOutlined, CloseOutlined } from '@vicons/material'
import { toast } from '../toast'

const props = defineProps<{
  show: boolean
  serverId: string
  path: string | null
}>()

const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'saved'): void
}>()

const content = ref('')
const initial = ref('')
const loading = ref(false)
const saving = ref(false)
const binary = ref(false)
const tooLarge = ref(false)
const size = ref(0)

const dirty = computed(() => content.value !== initial.value)
const API = computed(() => `/api/servers/${props.serverId}/files`)

const language = computed(() => {
  const ext = (props.path || '').toLowerCase().split('.').pop() || ''
  switch (ext) {
    case 'yml':
    case 'yaml':       return yaml()
    case 'json':       return json()
    case 'js':
    case 'mjs':
    case 'cjs':        return javascript()
    case 'ts':         return javascript({ typescript: true })
    case 'html':
    case 'htm':        return html()
    case 'css':        return css()
    case 'xml':        return xml()
    case 'md':
    case 'markdown':   return markdown()
    case 'properties':
    case 'conf':
    case 'cfg':
    case 'ini':
    case 'toml':       return StreamLanguage.define(properties)
    default:           return []
  }
})

const extensions = computed(() => [oneDark, language.value].flat())

async function load() {
  if (!props.path) return
  loading.value = true
  binary.value = false
  tooLarge.value = false
  content.value = ''
  initial.value = ''
  try {
    const qs = new URLSearchParams({ path: props.path })
    const res = await fetch(`${API.value}/read?${qs}`)
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    const data = await res.json()
    if (data.binary) {
      binary.value = true
      size.value = data.size
    } else if (data.too_large) {
      tooLarge.value = true
      size.value = data.size
    } else {
      content.value = data.content || ''
      initial.value = content.value
    }
  } catch (e: any) {
    toast.error('Lesen fehlgeschlagen', e.message)
    emit('update:show', false)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!props.path || binary.value || tooLarge.value) return
  saving.value = true
  try {
    const res = await fetch(`${API.value}/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: props.path, content: content.value }),
    })
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    initial.value = content.value
    toast.success('Gespeichert', props.path)
    emit('saved')
  } catch (e: any) {
    toast.error('Speichern fehlgeschlagen', e.message)
  } finally {
    saving.value = false
  }
}

function close() {
  if (dirty.value && !confirm('Ungespeicherte Änderungen verwerfen?')) return
  emit('update:show', false)
}

watch(() => [props.show, props.path], () => {
  if (props.show) load()
}, { immediate: true })
</script>

<template>
  <NModal
    :show="show"
    @update:show="(v) => { if (!v) close(); else emit('update:show', v) }"
    preset="card"
    style="width: 92vw; max-width: 1400px; height: 88vh;"
    :bordered="false"
    :mask-closable="false"
  >
    <template #header>
      <div class="flex items-center gap-2 text-sm font-mono">
        <span class="text-fg font-sans font-medium">Editor</span>
        <span class="text-dim">·</span>
        <span class="text-muted truncate">{{ path }}</span>
        <span v-if="dirty" class="text-warning text-xs font-sans">● ungespeichert</span>
      </div>
    </template>

    <NSpin :show="loading" class="h-full">
      <div v-if="binary" class="flex flex-col items-center justify-center h-full gap-2 text-muted">
        <p>Binärdatei – kann nicht bearbeitet werden.</p>
        <p class="text-sm text-dim">{{ size }} Bytes</p>
      </div>
      <div v-else-if="tooLarge" class="flex flex-col items-center justify-center h-full gap-2 text-muted">
        <p>Datei zu groß ({{ size }} Bytes, Limit 1 MB).</p>
        <p class="text-sm text-dim">Bitte extern bearbeiten.</p>
      </div>
      <Codemirror
        v-else
        v-model="content"
        :extensions="extensions"
        :style="{ height: 'calc(88vh - 220px)', fontSize: '13px', borderRadius: '6px', overflow: 'hidden' }"
        :autofocus="true"
        :indent-with-tab="true"
        :tab-size="2"
      />
    </NSpin>

    <template #footer>
      <div class="flex justify-end gap-2">
        <NButton @click="close">
          <template #icon><NIcon><CloseOutlined /></NIcon></template>
          Schließen
        </NButton>
        <NButton
          type="primary"
          :loading="saving"
          :disabled="binary || tooLarge || loading || !dirty"
          @click="save"
        >
          <template #icon><NIcon><SaveOutlined /></NIcon></template>
          Speichern
        </NButton>
      </div>
    </template>
  </NModal>
</template>