<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { NIcon, NSpin } from 'naive-ui'
import { FolderOpenOutlined, ArrowBackOutlined } from '@vicons/material'
import { Filemanager, WillowDark, getMenuOptions } from '@svar-ui/vue-filemanager'
import type { TContextMenuType, IParsedEntity, IFileMenuOption } from '@svar-ui/vue-filemanager'
import '@svar-ui/vue-filemanager/all.css'
import FileEditor from '../components/FileEditor.vue'
import { toast } from '../toast'

// ---- Setup ----
const route = useRoute()
const id = route.params.id as string
const API = `/api/servers/${id}/files`
const simpleIcons: any = 'simple'

// ---- State ----
type FileEntry = {
  id: string
  type: 'folder' | 'file'
  size?: number
  date: Date
  lazy?: boolean
}

const api = ref<any>(null)
const loading = ref(true)
const data = ref<FileEntry[]>([])
const drive = ref({ used: 0, total: 0 })

const editorShow = ref(false)
const editorPath = ref<string | null>(null)

// ---- Helpers ----
function stripLeading(p: string) {
  return p.replace(/^\/+/, '')
}
function parentOf(p: string) {
  const idx = p.lastIndexOf('/')
  return idx <= 0 ? '/' : p.slice(0, idx)
}
function joinPath(parent: string, name: string) {
  const base = parent === '/' ? '' : parent
  return `${base}/${name}`.replace(/\/+/g, '/')
}

function mapEntry(e: any): FileEntry {
  const isDir = e.type === 'dir'
  return {
    id: '/' + e.rel.replace(/\\/g, '/'),
    type: isDir ? 'folder' : 'file',
    size: e.size ?? undefined,
    date: e.mtime ? new Date(e.mtime) : new Date(),
    ...(isDir ? { lazy: true } : {}),
  }
}

async function fetchListing(path: string) {
  const qs = new URLSearchParams({ path })
  const res = await fetch(`${API}?${qs}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function postJSON(suffix: string, body: unknown) {
  const res = await fetch(`${API}${suffix}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => res.statusText)
    throw new Error(txt || `${res.status}`)
  }
}

// ---- Laden ----
async function loadFiles() {
  loading.value = true
  try {
    const listing = await fetchListing('')
    data.value = (listing.entries || []).map(mapEntry)
  } catch (e: any) {
    toast.error('Dateien laden fehlgeschlagen', e.message)
  } finally {
    loading.value = false
  }
}

// ---- SVAR: Lazy Loading ----
async function onRequestData({ id }: { id: string }) {
  try {
    const listing = await fetchListing(stripLeading(id))
    const children = (listing.entries || []).map(mapEntry)
    api.value?.exec('provide-data', { data: children, id })
  } catch (e: any) {
    toast.error('Ordner laden fehlgeschlagen', e.message)
  }
}

// ---- SVAR: File Actions ----
async function onCreateFile({ id: parent, name }: { id: string; name: string }) {
  const path = joinPath(parent, name)
  try {
    await postJSON('/write', { path: stripLeading(path), content: '' })
    toast.success('Datei erstellt', path)
    await loadFiles()
  } catch (e: any) {
    toast.error('Erstellen fehlgeschlagen', e.message)
  }
}

async function onCreateFolder({ id: parent, name }: { id: string; name: string }) {
  try {
    await postJSON('/mkdir', { parent: stripLeading(parent), name })
    toast.success('Ordner erstellt', name)
    await loadFiles()
  } catch (e: any) {
    toast.error('Ordner erstellen fehlgeschlagen', e.message)
  }
}

async function onRenameFile({ id: oldId, name: newName }: { id: string; name: string }) {
  const newPath = joinPath(parentOf(oldId), newName)
  try {
    await postJSON('/copy', { src: stripLeading(oldId), dst: stripLeading(newPath), move: true })
    toast.success('Umbenannt', newName)
    await loadFiles()
  } catch (e: any) {
    toast.error('Umbenennen fehlgeschlagen', e.message)
  }
}

async function onDeleteFiles({ ids }: { ids: string[] }) {
  try {
    for (const raw of ids) {
      await postJSON('/delete', { path: stripLeading(raw) })
    }
    toast.success('Gelöscht', `${ids.length} Eintrag/Einträge`)
    await loadFiles()
  } catch (e: any) {
    toast.error('Löschen fehlgeschlagen', e.message)
  }
}

async function onCopyFiles({ ids, target }: { ids: string[]; target: string }) {
  try {
    for (const src of ids) {
      const name = src.split('/').pop() || 'copy'
      const dst = joinPath(target, name)
      await postJSON('/copy', { src: stripLeading(src), dst: stripLeading(dst), move: false })
    }
    toast.success('Kopiert', `${ids.length} Eintrag/Einträge`)
    await loadFiles()
  } catch (e: any) {
    toast.error('Kopieren fehlgeschlagen', e.message)
  }
}

async function onMoveFiles({ ids, target }: { ids: string[]; target: string }) {
  try {
    for (const src of ids) {
      const name = src.split('/').pop() || 'moved'
      const dst = joinPath(target, name)
      await postJSON('/copy', { src: stripLeading(src), dst: stripLeading(dst), move: true })
    }
    toast.success('Verschoben', `${ids.length} Eintrag/Einträge`)
    await loadFiles()
  } catch (e: any) {
    toast.error('Verschieben fehlgeschlagen', e.message)
  }
}

async function onUploadFile({ id: parent, file }: { id: string; file: File }) {
  const form = new FormData()
  form.append('file', file)
  const qs = new URLSearchParams({ path: stripLeading(parent) })
  try {
    const res = await fetch(`${API}/upload?${qs}`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    toast.success('Hochgeladen', file.name)
    await loadFiles()
  } catch (e: any) {
    toast.error('Upload fehlgeschlagen', e.message)
  }
}

async function onDownloadFile({ id: fileId }: { id: string }) {
  const qs = new URLSearchParams({ path: stripLeading(fileId) })
  window.location.href = `${API}/download?${qs}`
}

function onOpenFile({ id: fileId }: { id: string }) {
  editorPath.value = stripLeading(fileId)
  editorShow.value = true
}

// ---- SVAR: Context Menu ----
function menuOptions(mode: TContextMenuType, item?: IParsedEntity): IFileMenuOption[] {
  const defaults = getMenuOptions(mode) as unknown as IFileMenuOption[]
  if (mode !== 'file' || !item) return defaults

  return [
    {
      icon: 'wxi-edit',
      text: 'Open',
      hotkey: 'Ctrl+O',
      id: 'open',
      handler: () => onOpenFile({ id: (item as any).id }),
    } as IFileMenuOption,
    { type: 'separator' } as IFileMenuOption,
    ...defaults,
  ]
}

onMounted(loadFiles)
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
      <NIcon :size="20"><FolderOpenOutlined /></NIcon>
      Dateien
    </h1>

    <NSpin :show="loading">
      <div class="rounded-lg overflow-hidden bg-surface" style="height: calc(100vh - 200px);">
        <WillowDark>
          <Filemanager
            ref="api"
            :data="data"
            :drive="drive"
            :icons="simpleIcons"
            :menuOptions="menuOptions"
            :onrequestdata="onRequestData"
            :oncreatefile="onCreateFile"
            :oncreatefolder="onCreateFolder"
            :onrenamefile="onRenameFile"
            :ondeletefiles="onDeleteFiles"
            :oncopyfiles="onCopyFiles"
            :onmovefiles="onMoveFiles"
            :onuploadfile="onUploadFile"
            :ondownloadfile="onDownloadFile"
            :onopenfile="onOpenFile"
          />
        </WillowDark>
      </div>
    </NSpin>

    <FileEditor
      v-model:show="editorShow"
      :server-id="id"
      :path="editorPath"
      @saved="loadFiles"
    />
  </div>
</template>