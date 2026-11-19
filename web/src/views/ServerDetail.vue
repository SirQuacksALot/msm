<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { NCard, NButton, NIcon, NTag, NSpin } from 'naive-ui'
import {
  PlayArrowRound, StopRound, RefreshOutlined,
  ArrowBackOutlined, TerminalOutlined, FolderOpenOutlined
} from '@vicons/material'
import ConsoleTerminal from '../components/ConsoleTerminal.vue'
import { toast } from '../toast'

const route = useRoute()
const id = route.params.id as string

const loading = ref(true)
const server = ref<any>(null)
const busy = ref(false)

async function load() {
  try {
    const r = await fetch(`/api/servers/${id}`)
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    server.value = await r.json()
  } catch (e: any) {
    toast.error('Laden fehlgeschlagen', e.message)
  } finally {
    loading.value = false
  }
}

async function action(path: string, label: string) {
  busy.value = true
  try {
    const r = await fetch(`/api/servers/${id}/${path}`, { method: 'POST' })
    const j = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(j.detail || r.statusText)
    toast.success(`${label} erfolgreich`)
    await load()
  } catch (e: any) {
    toast.error(`${label} fehlgeschlagen`, e.message)
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div>
      <RouterLink
        to="/"
        class="text-muted hover:text-muted-hover text-sm inline-flex items-center gap-1 transition-colors"
      >
        <NIcon :size="16"><ArrowBackOutlined /></NIcon>
        Übersicht
      </RouterLink>
    </div>

    <div class="flex items-start justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-semibold text-fg">{{ server?.instance?.display_name || id }}</h1>
        <p class="text-muted text-sm font-mono mt-0.5">{{ server?.instance?.container_name }}</p>
      </div>
      <div class="flex gap-2 items-center flex-wrap">
        <NTag v-if="server" :type="server.status === 'running' ? 'success' : 'default'" round>
          <span class="font-mono">{{ server.status }}</span>
        </NTag>
        <NButton size="small" @click="action('start', 'Start')" :disabled="server?.status === 'running' || busy">
          <template #icon><NIcon><PlayArrowRound /></NIcon></template>
          Start
        </NButton>
        <NButton size="small" @click="action('stop', 'Stop')" :disabled="server?.status !== 'running' || busy">
          <template #icon><NIcon><StopRound /></NIcon></template>
          Stop
        </NButton>
        <NButton size="small" @click="action('restart', 'Restart')" :disabled="server?.status !== 'running' || busy">
          <template #icon><NIcon><RefreshOutlined /></NIcon></template>
          Restart
        </NButton>
      </div>
    </div>

    <NSpin :show="loading">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <NCard title="Info" size="small" class="lg:col-span-1" :bordered="false">
          <div v-if="server" class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-muted">Template</span>
              <span class="font-mono">{{ server.instance.template }}</span>
            </div>
            <div class="flex justify-between gap-2">
              <span class="text-muted shrink-0">Container</span>
              <span class="font-mono text-xs truncate">{{ server.instance.container_name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted">Status</span>
              <span class="font-mono">{{ server.status }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted">Health</span>
              <span class="font-mono">{{ server.health || '–' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted">ID</span>
              <span class="font-mono text-xs">{{ server.id }}</span>
            </div>
            <div class="pt-3 border-t border-border mt-3">
              <RouterLink
                :to="`/servers/${id}/files`"
                class="text-accent hover:text-accent-hover text-sm inline-flex items-center gap-1.5 transition-colors"
              >
                <NIcon :size="16"><FolderOpenOutlined /></NIcon>
                Dateien öffnen
              </RouterLink>
            </div>
          </div>
        </NCard>

        <NCard size="small" class="lg:col-span-2" :bordered="false" content-style="padding: 12px;">
          <template #header>
            <div class="flex items-center gap-2 text-muted">
              <NIcon :size="18"><TerminalOutlined /></NIcon>
              <span>Konsole</span>
            </div>
          </template>
          <ConsoleTerminal :id="id" height="420px" />
        </NCard>
      </div>
    </NSpin>
  </div>
</template>