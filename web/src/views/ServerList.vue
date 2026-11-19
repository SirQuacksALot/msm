<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NButton, NCard, NIcon, NTag, NSpin, NEmpty } from 'naive-ui'
import { RouterLink } from 'vue-router'
import {
  PlayArrowRound, StopRound, RefreshOutlined, ArrowForwardOutlined,
} from '@vicons/material'
import { getServers, startServer, stopServer, restartServer, type Server } from '../api'
import { toast } from '../toast'

const servers = ref<Server[]>([])
const loading = ref(true)
const busy = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    servers.value = await getServers()
  } catch (e: any) {
    toast.error('Laden fehlgeschlagen', e.message)
  } finally {
    loading.value = false
  }
}

async function action(id: string, fn: (id: string) => Promise<void>, label: string, ev: Event) {
  ev.preventDefault()
  ev.stopPropagation()
  busy.value = id
  try {
    await fn(id)
    toast.success(`${label} erfolgreich`)
    await load()
  } catch (e: any) {
    toast.error(`${label} fehlgeschlagen`, e.message)
  } finally {
    busy.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex items-end justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-fg">Server</h1>
        <p class="text-muted text-sm mt-0.5">Minecraft-Server in diesem Compose-Stack</p>
      </div>
      <NButton size="small" @click="load" :loading="loading">
        <template #icon><NIcon><RefreshOutlined /></NIcon></template>
        Aktualisieren
      </NButton>
    </div>

    <NSpin :show="loading">
      <NEmpty
        v-if="!loading && servers.length === 0"
        description="Keine Minecraft-Server im Stack gefunden"
      />

      <div v-else class="grid gap-4 grid-cols-1 md:grid-cols-2">
        <NCard v-for="s in servers" :key="s.id" hoverable :bordered="false">
          <template #header>
            <div class="flex items-center justify-between gap-2">
              <RouterLink
                :to="`/servers/${s.id}`"
                class="text-fg hover:text-fg-hover font-medium truncate transition-colors"
              >
                {{ s.display_name }}
              </RouterLink>
              <NTag
                :type="s.status === 'running' ? 'success' : s.status === 'exited' ? 'error' : 'warning'"
                size="small"
                round
              >
                <span class="font-mono">{{ s.status }}</span>
              </NTag>
            </div>
          </template>

          <div class="text-xs text-muted space-y-1 mb-4 font-mono">
            <div class="flex justify-between">
              <span class="font-sans">Template</span>
              <span class="text-muted">{{ s.template }}</span>
            </div>
            <div class="flex justify-between">
              <span class="font-sans">Container</span>
              <span class="text-muted">{{ s.container_id }}</span>
            </div>
            <div class="flex justify-between">
              <span class="font-sans">Health</span>
              <span class="text-muted">{{ s.health || '–' }}</span>
            </div>
          </div>

          <div class="flex gap-2 flex-wrap items-center">
            <NButton
              size="small"
              @click="(ev) => action(s.id, startServer, 'Start', ev)"
              :disabled="s.status === 'running' || busy === s.id"
            >
              <template #icon><NIcon><PlayArrowRound /></NIcon></template>
              Start
            </NButton>
            <NButton
              size="small"
              @click="(ev) => action(s.id, stopServer, 'Stop', ev)"
              :disabled="s.status !== 'running' || busy === s.id"
            >
              <template #icon><NIcon><StopRound /></NIcon></template>
              Stop
            </NButton>
            <NButton
              size="small"
              @click="(ev) => action(s.id, restartServer, 'Restart', ev)"
              :disabled="s.status !== 'running' || busy === s.id"
            >
              <template #icon><NIcon><RefreshOutlined /></NIcon></template>
              Restart
            </NButton>
            <RouterLink :to="`/servers/${s.id}`" class="ml-auto">
              <NButton size="small" type="primary">
                Öffnen
                <template #icon><NIcon><ArrowForwardOutlined /></NIcon></template>
              </NButton>
            </RouterLink>
          </div>
        </NCard>
      </div>
    </NSpin>
  </div>
</template>