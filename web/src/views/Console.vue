<script setup lang="ts">
import { useRoute, RouterLink } from 'vue-router'
import { NIcon } from 'naive-ui'
import { ArrowBackOutlined, TerminalOutlined } from '@vicons/material'
import ConsoleTerminal from '../components/ConsoleTerminal.vue'

const route = useRoute()
const id = route.params.id as string
</script>

<template>
  <div>
    <RouterLink
      :to="`/servers/${id}`"
      class="text-muted hover:text-muted-hover text-sm inline-flex items-center gap-1 mb-2 transition-colors"
    >
      <NIcon :size="16"><ArrowBackOutlined /></NIcon>
      zurück
    </RouterLink>
    <h1 class="text-xl font-semibold mb-4 text-fg flex items-center gap-2">
      <NIcon :size="20"><TerminalOutlined /></NIcon>
      Konsole: <span class="font-mono text-muted">{{ id }}</span>
    </h1>
    <ConsoleTerminal :id="id" height="calc(100vh - 240px)" />
  </div>
</template>