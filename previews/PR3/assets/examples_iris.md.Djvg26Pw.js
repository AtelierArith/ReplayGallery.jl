import{_ as n,C as e,o as l,c as t,j as a,a as p,E as r,ao as h}from"./chunks/framework.Cn6sND6h.js";const E=JSON.parse('{"title":"Iris dataset","description":"","frontmatter":{},"headers":[],"relativePath":"examples/iris.md","filePath":"examples/iris.md","lastUpdated":null}'),k={name:"examples/iris.md"};function d(c,s,o,F,g,u){const i=e("AsciinemaPlayer");return l(),t("div",null,[s[0]||(s[0]=a("h1",{id:"Iris-dataset",tabindex:"-1"},[p("Iris dataset "),a("a",{class:"header-anchor",href:"#Iris-dataset","aria-label":'Permalink to "Iris dataset {#Iris-dataset}"'},"​")],-1)),s[1]||(s[1]=a("p",null,"Validated recording for these source inputs.",-1)),r(i,{src:"/recordings/iris.cast"}),s[2]||(s[2]=h(`<ul><li><p><a href="https://github.com/AtelierArith/ReplayGallery.jl/tree/main/examples/iris" target="_blank" rel="noreferrer">Source and dependencies</a></p></li><li><p><a href="https://github.com/AtelierArith/ReplayGallery.jl/blob/main/recordings/iris.cast" target="_blank" rel="noreferrer">Cast file</a></p></li><li><p><a href="https://github.com/AtelierArith/ReplayGallery.jl/blob/main/recordings/provenance.json" target="_blank" rel="noreferrer">Provenance</a></p></li></ul><h2 id="Record-this-example" tabindex="-1">Record this example <a class="header-anchor" href="#Record-this-example" aria-label="Permalink to &quot;Record this example {#Record-this-example}&quot;">​</a></h2><div class="language-sh vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">sh</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">python</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> scripts/record.py</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> iris</span></span></code></pre></div><h2 id="Source" tabindex="-1">Source <a class="header-anchor" href="#Source" aria-label="Permalink to &quot;Source {#Source}&quot;">​</a></h2><div class="language-julia vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">julia</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">using</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> Replay</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">instructions </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> raw</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using OhMyREPL</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using LinearAlgebra</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using Printf</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using Statistics</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using DataFrames</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using RDatasets</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">using StatsPlots</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"># use UnicodePlots.jl as backend</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">unicodeplots();</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">iris = dataset(&quot;datasets&quot;, &quot;iris&quot;);</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">@show names(iris);</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">N = size(iris, 1)</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">@show names(iris);</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"># Execute PCA</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">X = Matrix(select(iris, Not(:Species)))</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">X .= X .- mean(X, dims=1)</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">Σ = (X&#39; * X)/N # will be the covariance matrix for iris dataset</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">e = eigen(Σ, sortby = -);</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"># display  eigen values in descending order</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">e.values</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"># eigen vectors</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">e.vectors</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">@printf &quot;1st contribution ratio = %.2f percent</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">\\n</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot; 100e.values[1]/sum(e.values)</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">@printf &quot;2nd contribution ratio = %.2f percent</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">\\n</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot; 100e.values[2]/sum(e.values)</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"># Visualize the reduced data via PCA</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">topk = 2;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">reduced_data = DataFrame(X * e.vectors[:, 1:topk], [:X, :Y]);</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">@df reduced_data scatter(:X, :Y, group=iris.Species)</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;&quot;&quot;</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">replay</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(instructions, use_ghostwriter</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">true</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, julia_project</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">@__DIR__</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span></code></pre></div>`,5))])}const C=n(k,[["render",d]]);export{E as __pageData,C as default};
