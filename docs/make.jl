using Documenter
using DocumenterVitepress
using JSON

const ROOT = normpath(joinpath(@__DIR__, ".."))
const REPO = "github.com/AtelierArith/ReplayGallery.jl"
const REPO_URL = "https://$REPO"
const DEPLOY_URL = "https://atelierarith.github.io/ReplayGallery.jl"
const SOURCE = joinpath(@__DIR__, "src")
const TEMPLATES = joinpath(@__DIR__, "templates")
const EXAMPLE_PAGES = joinpath(SOURCE, "examples")

# ステータスごとの説明文。`scripts/gallery.py describe` が返すコードに対応する。
const STATUS_TEXT = Dict(
    "validated" => "Validated recording for these source inputs.",
    "stale" => "Stale recording: source inputs have changed; rerun recording CI.",
    "historical" => "Historical recording migrated from Replay.jl (not revalidated against current dependencies).",
    "missing" => "No reviewed recording yet. Run the example or download the recording workflow artifact; missing output is not a validation pass.",
    "sixel" => "SIXEL rendering is not supported by the browser player. Run this example in a SIXEL-capable terminal; it is not part of recording CI.",
)

const STATUS_LABEL = Dict(
    "validated" => "Validated",
    "stale" => "Stale",
    "historical" => "Historical",
    "missing" => "No recording",
    "sixel" => "SIXEL",
)

"""
Vitepress にギャラリー用の Vue コンポーネントと静的ファイルを登録するプラグイン。

`assets` ディレクトリの内容が Vitepress の `public/` にコピーされる
（このサイトでは `asciinema/` と `recordings/` を置いている）。
"""
struct GalleryPlugin <: Documenter.Plugin
    assets::String
end

DocumenterVitepress.vitepress_components(::GalleryPlugin) = [
    (name = "AsciinemaPlayer", import_path = "@/AsciinemaPlayer.vue"),
]

DocumenterVitepress.vitepress_assets(plugin::GalleryPlugin) = [plugin.assets]

# 例のページは examples/ と recordings/ から生成するため、GitHub の
# "Edit this page" リンク先が存在しない。無効化しておく。
DocumenterVitepress.vitepress_config_transform(::GalleryPlugin, config::String) =
    replace(config, r"editLink: \{[^\n]*\}" => "editLink: false")

"""
カタログ・キャスト・provenance の検証込みでギャラリーの一覧を取得する。

ハッシュ計算やステータス判定を Python 側（`scripts/gallery.py`）に一元化するため、
JSON を返すだけの薄いラッパーにしてある。
"""
function gallery_manifest()
    script = joinpath(ROOT, "scripts", "gallery.py")
    isfile(script) || error("gallery catalog script is missing: $script")
    python = something(Sys.which("python3"), Sys.which("python"), nothing)
    isnothing(python) && error("python3 is required to build the gallery documentation")
    return JSON.parse(read(`$python $script describe`, String))
end

"""
コードブロックを安全に囲えるフェンス長を返す（本文に ``` が含まれていても壊れない）。
"""
function code_fence(code::AbstractString)
    longest = maximum((length(m.match) for m in eachmatch(r"`+", code)); init = 0)
    return repeat("`", max(longest + 1, 3))
end

function write_example_page(entry)
    name = entry["name"]
    status = entry["status"]
    io = IOBuffer()

    println(io, "# ", entry["title"], "\n")
    println(io, get(STATUS_TEXT, status, ""), "\n")

    if entry["cast"]
        println(io, "```@raw html")
        println(io, "<AsciinemaPlayer src=\"/recordings/", name, ".cast\" />")
        println(io, "```\n")
    end

    println(io, "- [Source and dependencies]($REPO_URL/tree/main/examples/$name)")
    entry["cast"] && println(io, "- [Cast file]($REPO_URL/blob/main/recordings/$name.cast)")
    println(io, "- [Provenance]($REPO_URL/blob/main/recordings/provenance.json)\n")

    if entry["record"]
        println(io, "## Record this example\n")
        println(io, "```sh")
        println(io, "python scripts/record.py ", name)
        println(io, "```\n")
    end

    println(io, "## Source\n")
    fence = code_fence(entry["source"])
    println(io, fence, "julia")
    println(io, rstrip(entry["source"]))
    println(io, fence)

    path = joinpath(EXAMPLE_PAGES, "$name.md")
    write(path, String(take!(io)))
    return path
end

function examples_table(entries)
    io = IOBuffer()
    println(io, "| Example | Recording |\n| --- | --- |")
    for entry in entries
        label = get(STATUS_LABEL, entry["status"], entry["status"])
        println(io, "| [", entry["title"], "](./examples/", entry["name"], ".md) | ", label, " |")
    end
    return String(take!(io))
end

"""
生成物の Markdown と、Vitepress の public/ に置く静的ファイルを準備する。
"""
function prepare(entries)
    rm(EXAMPLE_PAGES; recursive = true, force = true)
    mkpath(EXAMPLE_PAGES)
    foreach(write_example_page, entries)

    template = read(joinpath(TEMPLATES, "index.md"), String)
    index = replace(template, "{{EXAMPLES}}" => examples_table(entries))
    write(joinpath(SOURCE, "index.md"), index)

    # `docs/video.md` はリポジトリ直下のドキュメントとして参照されているので、
    # サイト用にコピーする（元ファイルはそのまま残す）。
    cp(joinpath(@__DIR__, "video.md"), joinpath(SOURCE, "video.md"); force = true)

    assets = mktempdir()
    mkpath(joinpath(assets, "asciinema"))
    mkpath(joinpath(assets, "recordings"))
    for file in ("asciinema-player.min.js", "asciinema-player.css", "asciinema-player.LICENSE")
        cp(joinpath(ROOT, "assets", file), joinpath(assets, "asciinema", file))
    end
    for cast in readdir(joinpath(ROOT, "recordings"); join = true)
        endswith(cast, ".cast") && cp(cast, joinpath(assets, "recordings", basename(cast)))
    end
    return assets
end

entries = gallery_manifest()
assets = prepare(entries)
atexit(() -> rm(assets; recursive = true, force = true))

example_pages = ["$(entry["title"])" => "examples/$(entry["name"]).md" for entry in entries]

makedocs(;
    authors = "SatoshiTerasaki <terasakisatoshi.math@gmail.com>",
    repo = REPO_URL,
    sitename = "ReplayGallery.jl",
    format = DocumenterVitepress.MarkdownVitepress(;
        repo = REPO,
        devbranch = "main",
        devurl = "dev",
        deploy_url = DEPLOY_URL,
        description = "Reproducible Julia terminal examples recorded with Replay.jl.",
        write_inventory = false,
    ),
    plugins = [GalleryPlugin(assets)],
    pages = [
        "Home" => "index.md",
        "Examples" => example_pages,
        "Recording guide" => "recording.md",
        "Exporting video" => "video.md",
    ],
    warnonly = true,
)

DocumenterVitepress.deploydocs(;
    repo = REPO,
    devbranch = "main",
    push_preview = true,
)
