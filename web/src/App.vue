<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
import { NConfigProvider, NIcon, darkTheme } from 'naive-ui'
import { Toaster } from 'vue-sileo'
import 'vue-sileo/styles.css'
import { getThemeOverrides } from './theme'
import { GridViewOutlined } from '@vicons/material'
import { Github } from '@vicons/fa'
import { OpenInNewOutlined } from '@vicons/material'
import ServerNavbar from './components/ServerNavbar.vue'

const themeOverrides = getThemeOverrides()
</script>

<template>
  <NConfigProvider :theme="darkTheme" :theme-overrides="themeOverrides">
    <div class="min-h-screen flex flex-col bg-bg text-fg">
      <header class="bg-bg/85 backdrop-blur sticky top-0 z-20">
        <div class="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <RouterLink
            to="/"
            class="font-semibold text-lg text-fg hover:text-fg-hover transition-colors flex items-center gap-2.5"
          >
            <NIcon :size="22" class="text-accent"><GridViewOutlined /></NIcon>
            <span>MC Stack Manager</span>
          </RouterLink>
          <span class="text-xs text-dim font-mono">docker stack</span>
        </div>
        
        <div class="max-w-6xl mx-auto px-6 pb-3">
          <ServerNavbar />
        </div>
      </header>

      <!-- Globale Server Navbar -->

      <main class="w-full max-w-6xl mx-auto px-6 py-8 flex-1">
        <RouterView :key="$route.fullPath" />
      </main>

      <Toaster
        position="top-right"
        theme="dark"
        :duration="4000"
        :options="{ fill: 'var(--color-elevated)', roundness: 10 }"
      />

      <footer class="h-14 shrink-0 border-t border-border">
        <div class="max-w-6xl mx-auto px-6 h-full flex items-center justify-between">
          <a
            href="https://github.com/SirQuacksALot/msm"
            target="_blank"
            rel="noopener noreferrer"
            class="text-xs text-muted hover:text-fg transition-colors flex items-center gap-2"
          >
            <NIcon :size="16"><Github /></NIcon>
            GitHub
            <NIcon :size="13"><OpenInNewOutlined /></NIcon>
          </a>
        </div>
      </footer>
    </div>
  </NConfigProvider>
</template>