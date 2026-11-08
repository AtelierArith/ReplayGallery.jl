<script setup>
// asciinema-player の薄い Vue ラッパー。`docs/make.jl` の Documenter.Plugin から
// グローバル登録される。プレイヤー本体は `assets/` の vendored ファイルを使う。
// 使い方: <AsciinemaPlayer src="/recordings/helloworld.cast" />
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps({
  /** .cast ファイルのパス（サイトルート基準）または絶対 URL */
  src: { type: String, required: true },
  /** 再生速度の倍率 */
  speed: { type: Number, default: 1 },
  /** 読み込み後に自動再生するか */
  autoplay: { type: Boolean, default: false },
  /** 再生前にキャストを先読みするか */
  preload: { type: Boolean, default: false },
  /** 最後まで再生したら繰り返すか */
  loop: { type: Boolean, default: false },
  /** 再生前に表示するフレーム（例: "npt:0:01"） */
  poster: { type: String, default: 'npt:0:01' },
  /** 再生時にスキップするアイドル時間（秒） */
  idleTimeLimit: { type: Number, default: 2 },
  /** 端末のフォントサイズ */
  terminalFontSize: { type: String, default: 'small' },
})

const PLAYER_JS = '/asciinema/asciinema-player.min.js'
const PLAYER_CSS = '/asciinema/asciinema-player.css'

const host = ref(null)
const failed = ref(false)
let player = null
let assetsPromise = null

function loadAssets() {
  if (window.AsciinemaPlayer) return Promise.resolve()
  if (assetsPromise) return assetsPromise

  assetsPromise = new Promise((resolve, reject) => {
    if (!document.querySelector('link[data-asciinema-player]')) {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = withBase(PLAYER_CSS)
      link.dataset.asciinemaPlayer = ''
      document.head.appendChild(link)
    }
    const script = document.createElement('script')
    script.src = withBase(PLAYER_JS)
    script.async = true
    script.dataset.asciinemaPlayer = ''
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`could not load ${PLAYER_JS}`))
    document.head.appendChild(script)
  })
  return assetsPromise
}

function resolveSrc(src) {
  // "https://..." のような絶対 URL はそのまま、それ以外は base を前置する
  return /^[a-z][a-z0-9+.-]*:/i.test(src) ? src : withBase(src)
}

onMounted(async () => {
  try {
    await loadAssets()
    player = window.AsciinemaPlayer.create(resolveSrc(props.src), host.value, {
      fit: 'width',
      speed: props.speed,
      autoplay: props.autoplay,
      preload: props.preload,
      loop: props.loop,
      poster: props.poster,
      idleTimeLimit: props.idleTimeLimit,
      terminalFontSize: props.terminalFontSize,
      terminalFontFamily:
        'JuliaMono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
    })
  } catch (err) {
    console.error('[AsciinemaPlayer]', err)
    failed.value = true
  }
})

onBeforeUnmount(() => {
  if (player) {
    player.dispose()
    player = null
  }
})
</script>

<template>
  <figure class="asciinema-figure">
    <div ref="host" class="asciinema-host"></div>
    <p v-if="failed" class="asciinema-error">
      Could not load the player for <code>{{ src }}</code
      >.
    </p>
    <figcaption v-if="$slots.default">
      <slot />
    </figcaption>
  </figure>
</template>

<style scoped>
.asciinema-figure {
  margin: 1.5rem 0;
}

.asciinema-host {
  min-height: 20rem;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
}

.asciinema-error {
  color: var(--vp-c-danger-1);
}

figcaption {
  margin-top: 0.5rem;
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
}
</style>
