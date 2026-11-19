
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NButton, NIcon, NSpin, NTooltip } from 'naive-ui'
import { RouterLink } from 'vue-router'
import {
  FolderOutlined,
  OpenInNewOutlined,
  RefreshOutlined,
} from '@vicons/material'
import { getServers, type Server } from '../api'
import { toast } from '../toast'

const servers = ref<Server[]>([])
const loading = ref(false)

async function load() {
  loading.value = true

  try {
    servers.value = await getServers()
  } catch (e: any) {
    toast.error('Server konnten nicht geladen werden', e.message)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <nav class="w-full">
    <div class="flex items-center gap-3 py-1">
      <!-- Server-Liste -->
      <div class="flex items-center gap-2 overflow-x-auto flex-1 min-w-0 pb-3 pt-1">

        <NSpin v-if="loading && !servers.length" size="small" />

        <div
          v-for="s in servers"
          :key="s.id"
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg
                 border border-border bg-background shrink-0"
        >
          <!-- Statuspunkt -->
          <span
            class="w-2 h-2 rounded-full shrink-0"
            :class="{
              'bg-green-500': s.status === 'running',
              'bg-red-500': s.status === 'exited',
              'bg-yellow-500': !['running', 'exited'].includes(s.status)
            }"
          />

          <!-- Servername -->
          <RouterLink
            :to="`/servers/${s.id}`"
            class="text-sm font-medium text-fg hover:text-fg-hover
                   transition-colors max-w-40 truncate"
          >
            {{ s.display_name }}
          </RouterLink>

          <!-- Öffnen -->
          <NTooltip trigger="hover">
            <template #trigger>
              <RouterLink :to="`/servers/${s.id}`">
                <NButton size="tiny" quaternary>
                  <template #icon>
                    <NIcon><OpenInNewOutlined /></NIcon>
                  </template>
                  Öffnen
                </NButton>
              </RouterLink>
            </template>
            Server öffnen
          </NTooltip>

          <!-- Files -->
          <RouterLink :to="`/servers/${s.id}/files`">
            <NButton size="tiny" quaternary>
              <template #icon>
                <NIcon><FolderOutlined /></NIcon>
              </template>
              Files
            </NButton>
          </RouterLink>
        </div>

        <span
          v-if="!loading && servers.length === 0"
          class="text-xs text-muted"
        >
          Keine Instanzen gefunden
        </span>
      </div>

      <!-- Aktualisieren -->
      <NButton
        size="tiny"
        quaternary
        circle
        :loading="loading"
        @click="load"
      >
        <template #icon>
          <NIcon><RefreshOutlined /></NIcon>
        </template>
      </NButton>

    </div>
  </nav>
</template>
