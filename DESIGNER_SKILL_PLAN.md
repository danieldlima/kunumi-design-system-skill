# Designer local na skill Kosmos — plano de implementação

## Context

O repo `kosmos-design-system-skill` hoje é **conhecimento + lookup**: `SKILL.md` roteia para
`references/`, e `kunumi_lookup.py` resolve tokens, assets, slides e patterns.

O que falta é o loop de um designer. A linha mais importante do `SKILL.md` — *"Render the final
artifact and inspect every page, slide, frame, loop, breakpoint, or export at delivery size"* — é
hoje **instrução em prosa sem ferramenta por trás e sem verificação**. A assimetria central:
`scripts/validate-skills.py` valida **o repo da skill**, nunca **o que a skill produz**. O linter
aponta para dentro.

Três provas disso já estão commitadas e ninguém detectou, porque nada verifica artefato:

1. `template-preview.html:~283` — `.instituto-cover .slide__logo { filter: brightness(0) invert(1) }`
   **recolore uma marca aprovada via CSS**, violando a proibição 4 de `logo-governance.md` e o
   inegociável "do not recolor" do próprio `SKILL.md`.
2. `.kunumi-title { line-height: 1.55 }` está fora de `typography.lineHeightRanges.display`
   (`"110% - 140%"`).
3. `template-preview.png` e `template-preview-instituto.png` são **JPEGs com extensão `.png`**,
   defasados (mtime 19/ago contra HTML 20/ago e CSS 24/ago), e mostram a headline em **caixa baixa,
   em Figtree** — contra a regra de display e contra o próprio CSS atual.

**Objetivo**: construir o núcleo `propor → renderizar → lintar → criticar visualmente → corrigir`,
acionável como skill local, provando valor antes de decidir MCP ou subagente. O plano marca qual
fronteira de módulo vira superfície MCP depois.

## Decisões de escopo (confirmadas)

| Questão | Decisão |
|---|---|
| Modo v1 | **Gerar do zero** a partir de briefing — `create` é a porta de entrada |
| Saída | **HTML, PNG e Penpot** selecionáveis, um ou mais por invocação |
| Escopo de design | Qualquer artefato Kunumi, **100% web**. Nada de impressão |
| Cobertura do lint | **Visual primeiro** — cor, tipografia, geometria, logo, motion, gráfico. Copy fica para a fase 5 |
| Crítica | **Lint + render + visão** — o agente olha o PNG |
| Invocação | **Skill separada** `kosmos-designer` no mesmo plugin |

Consequência do "web only": saem MDC, formatos em mm, CMYK/Pantone e mínimo de 10 mm. Fica o
mínimo de logo em **28 px**.

## Princípios de desenho

**1. Derivar regras do `tokens.json`, nunca hardcodar.** O arquivo já é base de regras legível por
máquina: `color.prohibition` com as duas exceções estruturadas, `typography.variables[]` com `case`
e `letterSpacingPercent`, `typography.emphasis.forbiddenOn: "titles"`, `lineHeightRanges`,
`geometry.spacing` com 13 passos. É exatamente onde `validate_tokens()` erra hoje — hardcoda
`--kunumi-instituto-black` e `--kunumi-surface-raised` em Python.

**2. Precisão é o produto; cobertura não é.** Um linter de "hex não aprovado" morre na primeira
semana neste repo, por causa de **tensões documentadas** (não bugs): a paleta Ksequence de
`visual-patterns.md`; os `#000000`/`#FFFFFF` intencionais de `profile-photo-system.md`; o
Figtree/Arial herdado que `template-design-system.md` manda preservar em trabalho derivado de deck;
`--kunumi-leading-display: 1.2` divergindo de `1.1` de propósito. **E uma sexta**, achada na
exploração: `template-preview.html` mistura artefato e chrome de visualizador no mesmo arquivo
(`body { background: #11151a }`, `box-shadow` e `border-radius: 0.25rem` no `.stage`) — o que força
isenção **no nível de elemento**, não só de arquivo.

Daí o mecanismo de **escopo de regra** e a severidade `note`, que existe para o linter *falar* sem
gritar lobo. Ship **~15 regras**, não 40.

**3. Python decide o mecanicamente decidível; o agente decide gosto.** Python nunca chama Penpot,
nunca faz HTTP, nunca julga hierarquia.

---

## Arquitetura

### Layout em disco

```
skills/kosmos-design-system/                    ENGINE (mora junto do tokens.json)
  references/design-rules.json          NEW     schema kunumi.design-rules/v1
  scripts/
    kunumi_critic.py                    NEW     único entry point novo (6 subcomandos)
    kunumi_design/                      NEW     pacote; futura superfície MCP
      findings.py     Finding / Severity / Report / serialização
      rules.py        registry, resolução de escopo, derivação do tokens.json
      scan.py         extração de declaração CSS e nó/texto HTML (stdlib)
      render.py       probe de capacidade + HTML→PNG + medição de geometria
      checks/         color.py typography.py geometry.py logo.py motion.py artifact.py
      adapters/       html.py png.py penpot.py
  SKILL.md                              EDIT    +1 linha cruzando para a skill designer

skills/kosmos-designer/                         PROCEDIMENTO (skill nova)
  SKILL.md                              NEW     gatilho de ação, não de conhecimento
  references/
    design-loop.md                      NEW     o loop de 9 passos (~120 linhas)
    critique-checklist.md               NEW     o que a passagem de visão deve responder
  decisions/                            NEW     log ADR de precedente
    README.md  template.md  0001-*.md

scripts/validate-skills.py              EDIT    uma de-hardcodação cirúrgica
scripts/build_bundle.py                 KEEP    ja ignora DESIGNER_SKILL_PLAN.md (este plano)
pyproject.toml + uv.lock                NEW     deps só de dev/opcional; runtime segue stdlib
tests/                                  NEW     pytest + fixtures deliberadamente fora de norma
.github/workflows/checks.yml            NEW     fase 5
```

**Engine junto do `tokens.json`, procedimento na skill nova.** As regras derivam dos tokens, e
`validate-skills.py` vai importar do pacote — então o engine pertence a `kosmos-design-system`. A
skill `kosmos-designer` é procedimento puro e chama o script irmão por caminho resolvido.

**Custo real da escolha de duas skills** — duas coisas a acertar:
- `Path(__file__).resolve()` (convenção que o repo já usa) faz o caminho irmão funcionar tanto no
  symlink de dev quanto na cópia do marketplace. Sem `.resolve()`, quebra no symlink.
- O README avisa que instalações sobrepostas deixam "two copies competing to trigger". Mitigação:
  a `description` de `kosmos-designer` é **acional** ("produza/gere/revise um artefato executando o
  loop"), a de `kosmos-design-system` continua de **conhecimento**. Sem sobreposição de gatilho.
- `AGENTS.md` abre com "holding one skill" — precisa ser atualizado. `validate-skills.py` já itera
  sobre todos os diretórios de `skills/`, então a validação não muda.

Renders vão para `output/kunumi-design/<slug>/` **relativo ao CWD**, nunca ao diretório da skill —
a instalação de marketplace deve ser tratada como read-only. `.gitignore` já contém `output/`.

### O modelo `Finding`

`kunumi_design/findings.py`. Primeiro `@dataclass(frozen=True, slots=True)` e `Literal` do repo —
justificado porque seis módulos precisam de uma forma só, e dict solto reproduziria exatamente a
opacidade de `list[str]` que torna `validate-skills.py` difícil de estender.

```python
Severity = Literal["blocker", "violation", "advisory", "note"]

@dataclass(frozen=True, slots=True)
class Finding:
    rule: str               # "logo.no-effects" — pontuado, estável, grepável
    severity: Severity
    scope: str              # escopo sob o qual foi avaliado: "web.instituto"
    locus: str              # ".instituto-cover .slide__logo" / "frame:cover"
    path: str
    line: int | None        # 1-based; None quando é arquivo inteiro ou vem do render
    message: str
    fix: str
    observed: str | None = None
    expected: str | None = None
    authority: str = ""     # "logo-governance.md#the-seven-prohibitions"
```

`authority` é o mecanismo de confiança: todo finding cita o arquivo e a âncora de onde a regra vem,
então a resposta a um finding contestado é ler o extrato do brandbook — não apagar o check.

| Severidade | Significado | Afeta exit code |
|---|---|---|
| `blocker` | Proibição do brandbook sem exceção no escopo ativo. Recolorir marca, hex de gráfico como acento de UI, preto puro como fundo | sim (exit 2) |
| `violation` | Regra declarada quebrada, corrigível mecanicamente. Display fora de caixa alta, tracking negativo, radius 8px | sim (exit 1) |
| `advisory` | Camada de produto ou preferência. Hex literal onde existe token semântico, spacing fora da escala de 4px | não |
| `note` | Tensão documentada, trazida à superfície de propósito. Figtree herdado de deck, paleta Ksequence, render indisponível | não |

**Contrato `--json`** (camelCase, como os outros JSON do repo): `schema: "kunumi.design-report/v1"`,
`artifact`, `scope`, `scopeReason`, `counts{}`, `rulesEvaluated`, **`rulesSkipped[]`**, `renders[]`,
`findings[]`. Modo texto fecha com linha grepável, seguindo o `matches=N shown=M` do
`kunumi_lookup.py`:

```
blockers=1 violations=2 advisories=4 notes=1 scope=web.new renders=1
```

`rulesSkipped` é estrutural: **torna o silêncio auditável**. Escopo que suprime regra tem de dizer
quais.

**Não refatorar `validate-skills.py` para o `Finding`** — ele responde outra pergunta (o repo está
bem formado) para outro consumidor (gate humano pré-merge), e acoplar um script de higiene do repo a
um pacote que vive *dentro* do pacote da skill inverte a direção da dependência. Fazer **uma** mudança
cirúrgica: importar `rules.prohibition_exception_css_vars(tokens)` para parar de hardcodar os nomes
das exceções. Um import, uma mudança de comportamento. Fase 5, depois que o linter novo ganhar
confiança.

### O registry de regras

Duas fontes, unidas por `rules.load_registry(tokens) -> Registry`.

**(a) Derivadas** — funções puras sobre `tokens.json`; token muda, regra muda, zero Python editado.

```python
def derive_palette(tokens)            -> PaletteRules     # hexes aprovados por grupo, set de
                                                          # gráfico, superseded, assetLocal,
                                                          # prohibition + as duas exceções
def derive_typography(tokens)         -> TypographyRules   # famílias, fallbackOrder, tracking,
                                                          # case, "140% - 175%" -> (1.40, 1.75),
                                                          # emphasis.colors + forbiddenOn
def derive_geometry(tokens)           -> GeometryRules     # radii {"4px","10px"}, cardPadding,
                                                          # cardGap, textColumn, escala de 13
def derive_instituto_gradient(tokens) -> tuple[Stop, ...]  # 7 pares (hex, centrePercent)
```

Duas sutilezas a fixar agora, senão o linter contradiz o brandbook:
- `color.chart.seriesOrderObserved` é documentado como **não sendo regra** → no máximo `advisory`,
  marcado `observed-not-normative`.
- `geometry.cardPaddingNote` diz que 30px fica fora da escala de 4px **de propósito** → o check de
  spacing tem de excluir os valores de `geometry`, ou sinaliza o próprio número do brandbook.

**(b) Declaradas** — `references/design-rules.json`, para regras cuja autoridade é prosa (logo
28px, janelas de motion, 1584×396, fundo/tinta/grid de gráfico, teto de 5 séries). Dados, nunca `if`
em Python:

```json
{ "id": "logo.no-effects", "check": "declaration_forbidden_on_role", "severity": "blocker",
  "params": { "role": "logo",
              "properties": ["box-shadow", "text-shadow", "outline"],
              "functions": ["drop-shadow", "brightness", "invert", "hue-rotate", "grayscale"] },
  "authority": "logo-governance.md#the-seven-prohibitions",
  "fix": "Swap in the correct positive/negative mark file instead of filtering the mark." }
```

- `check` nomeia uma função em `CHECKS: dict[str, CheckFn]`. **Python é dono do mecanismo** (como
  achar uma declaração `border-radius`); **JSON é dono de valor, severidade, escopo e autoridade.**
  Nenhuma cadeia de dispatch por rule-id.
- `requires: ["render"]` marca regra dependente de medição, para entrar automaticamente em
  `rulesSkipped` quando não há renderer.
- `demote` (regra → severidade menor) é preferível a `relax` (regra → off) sempre que viável.
  Rebaixar mantém a observação e tira o alarme.

**Escopos** (`web.new` default, `web.deck-derived`, `web.chart`, `web.instituto`,
`web.profile-photo`, `web.ksequence`, `exempt`), cada um com `inherits`, `demote`/`relax`/`adds` e
um campo **`why` citando a autoridade**. Resolução espelha o Source Order do `SKILL.md`:

1. `--scope` na CLI (nomeado pelo usuário; ganha)
2. Declaração no artefato: `<html data-kunumi-scope>`, `<meta name="kunumi-scope">`, ou
   `/* kunumi-scope: ... */` no CSS
3. **Nível de elemento**: `data-kunumi-scope` estreita a subárvore; `data-kunumi-exempt` isenta —
   é isso que resolve a mistura artefato/chrome do `template-preview.html`
4. Inferência por caminho (`visual-patterns.md` → `web.ksequence`)
5. Default `web.new`

**Normalização de cor, resolvida no mecanismo e não por escopo.** O CSS do repo usa
`rgb(28 33 39 / 0.42)` (que **é** Chumbo a 42%) e `color-mix(in srgb, var(--kunumi-gelo) 72%,
transparent)`. O check tem de normalizar `#rgb`/`#rrggbb`/`rgb()`/`rgba()` e resolver `color-mix()`
de var única para o token base **antes** de declarar hex não aprovado. Sem isso, todo uso de alfa do
próprio repo é falso positivo no dia um.

### O renderer

**Playwright para Python dirigindo Chromium.** WeasyPrint e wkhtmltoimage estão fora: não suportam
`color-mix()`, tratam `clamp()` e `aspect-ratio` de forma inconsistente, e o tokens CSS usa os dois
intensamente — renderizariam **um artefato diferente do que vai ao ar**, e render em que não se
confia é pior que nenhum. O Chrome headless por CLI não dá clip por elemento, `deviceScaleFactor`,
espera de fonte, nem leitura de rect do DOM. Playwright dá os quatro: `emulate_media(reduced_motion)`,
`locator.bounding_box()` (**obrigatório** — com `clamp()` a altura do logo é estaticamente
indeterminável), `clip`, e `wait_for_function("document.fonts.ready")`.

**Dependência: `pyproject.toml` na raiz com `dependencies = []`, gerido por `uv`.**

```toml
[project]
requires-python = ">=3.11"
dependencies = []                      # o runtime da skill segue 100% stdlib
[project.optional-dependencies]
render = ["playwright>=1.44"]
[dependency-groups]
dev = ["pytest", "ruff", "playwright>=1.44"]
```

`dependencies = []` é a linha que sustenta tudo: o que um usuário de marketplace invoca
(`kunumi_lookup.py`, `kunumi_critic.py rules|lint|decisions`) continua stdlib. `uv` porque o
Konstrukt irmão já usa, já está no PATH, e `uv run --with playwright` executa sem `uv sync` prévio.
Verificado nesta máquina: **`~/Library/Caches/ms-playwright/chromium-1194` já está baixado** — custo
de download zero.

**Degradação — não pode quebrar para quem não tem Chromium.** `render.probe() -> RenderCapability`,
primeiro que casar ganha: playwright importável → `KUNUMI_RENDER_CMD` → `uv run --with playwright`
→ Chrome local (degradado, só página inteira) → indisponível. Quando indisponível, **`lint` roda e
sai normalmente**, emitindo um `note` com o comando de instalação e a lista de regras não avaliadas.
`render` **pode** falhar duro (`SystemExit` com a dica, como o repo já faz); `lint` **nunca**.

E um contrato de honestidade em `design-loop.md`: sem render, o agente **declara** isso na entrega e
não afirma verificação visual.

### Adaptadores de meio

**HTML é o meio autoral; PNG e Penpot derivam dele.** O repo já prova o modelo: `template-preview.html`
é autocontido, abrível em `file://`, sem build. Um IR só:

```python
@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    slug: str
    identity: Literal["kunumi", "unlimited", "instituto"]
    scope: str
    medium: tuple[str, ...]          # multi-seleção
    canvas: tuple[int, int]          # (1920, 1080) ou (1584, 396)
    html_path: Path                  # fonte de verdade de todo meio
    notes: str
```

- **`html`** — normaliza em `out_dir/<slug>.html`. Resolve todo href de asset por
  **`kunumi_lookup.resolved_source()`** (reuso: é o único resolvedor do repo e já devolve
  `localExists`/`absoluteLocalPath`). Garante o `<link>` do tokens CSS e ausência de URL de rede.
- **`png`** — delega a `render.py`. Um PNG por `[data-kunumi-frame]`, em `canvas` com
  `device_scale_factor` 2, **mais `out_dir/<slug>.render.json`** com a bounding box medida de todo
  `[data-kunumi-role]`. Esse JSON é o que os checks de medição consomem e o que acompanha a imagem
  na passagem de visão.
- **`penpot`** — **não produz arquivo nem faz chamada de rede.** Escreve
  `out_dir/<slug>.penpot-plan.json`: lista ordenada e declarativa de operações de shape, com o token
  que cada operação deve bindar. A skill então instrui o agente a executar via
  `mcp__penpot__execute_code` e trazer de volta com `mcp__penpot__export_shape` para
  `out_dir/<slug>-penpot.png` — **de modo que o mesmo lint + visão rode no round-trip do Penpot**.

| Dono | Responsabilidade |
|---|---|
| **Python** | Ler `tokens.json`. Resolver caminho de asset aprovado. Autorar/validar HTML. Renderizar PNG. Medir geometria. Avaliar toda regra declarativa. Emitir o plano Penpot e o relatório |
| **Agente (instruções da skill)** | Escrever o HTML inicial. Declarar escopo. Rodar `execute_code` e `export_shape`. **Olhar o PNG** e responder o checklist. Decidir e aplicar correção. Anexar o ADR |
| **Nunca Python** | Qualquer chamada Penpot, HTTP, credencial, ou juízo sobre hierarquia e gosto |

Python nunca importa cliente MCP. O pacote fica stdlib + um extra opcional, e a superfície MCP fica
*consumidora* do pacote, não dependência dele.

Multi-seleção com `action="append"`, como o `--tag` de `kunumi_lookup.py`:
`--medium html --medium png --medium penpot`, default `["html", "png"]`.

### O loop de criação

`skills/kosmos-designer/references/design-loop.md`, procedural, linkando em vez de repetir regra:

0. **Ler precedente** — `kunumi_critic.py decisions --search "<tema>"`. Antes de propor, não depois
1. **Enquadrar** — identidade, escopo, canvas, meios. Se escopo ≠ `web.new`, dizer por quê
2. **Propor** — escrever `output/kunumi-design/<slug>/<slug>.html`, com `<link>` no tokens CSS e
   todo asset vindo de `kunumi_lookup.py sources|assets`. Anotar `data-kunumi-frame` por entregável,
   `data-kunumi-role` por nó semântico, `data-kunumi-exempt` em chrome que não é artefato
3. **Renderizar** — `kunumi_critic.py render <html> --canvas 1920x1080`
4. **Lintar** — `kunumi_critic.py lint <html> --render <render.json> --scope <scope> --json`
5. **Ver** — abrir todo PNG com a ferramenta Read e responder `critique-checklist.md`
   **por escrito**. Obrigatório e não pulável; o relatório de lint não substitui
6. **Corrigir** — zerar blocker e violation. Para cada advisory/note, corrigir ou escrever uma frase
   de justificativa. Repetir 3–5. Teto de 3 ciclos, depois escalar
7. **Entregar** — declarar escopo usado, contagem de blocker, advisories remanescentes com
   justificativa, e **se o render de fato rodou**
8. **Registrar** — anexar ADR para todo juízo genuíno ou tensão de regra, e sempre para relaxamento
   de escopo

Não-objetivos a escrever no arquivo, para ninguém readicionar: nada de regra de impressão, MDC,
formato em mm, CMYK/Pantone, mínimo de 10 mm.

`critique-checklist.md` cobre exatamente o resíduo de julgamento, como **perguntas fechadas com
condição de falha declarada** — não "isso está bonito": hierarquia visual e mensagem dominante única;
ordem de leitura; um trabalho por vista; Urucum como acento seletivo ou preenchimento generalizado;
clear space do logo (1X, proporcional — medido do `render.json`, já que nenhum valor em px é
publicado); marca sobre fotografia; equilíbrio de altura óptica em co-branding; densidade e respiro.

### Log de precedente

`skills/kosmos-designer/decisions/`, **dentro do pacote da skill** — a instalação de dev symlinka o
diretório da skill em `~/.claude/skills/`, então um `decisions/` na raiz do repo seria inalcançável
em tempo de execução. E o designer precisa **ler** precedente antes de propor, o que o torna
"resource an agent needs at execution time" pelo `AGENTS.md`. Não adicionar à lista de ignore de
`build_bundle.py` — precedente acumulado é o valor.

ADR-lite com frontmatter parseável, reusando a forma de `parse_frontmatter()` que já existe em
`validate-skills.py`: `id, status, date, scope, artifact, rules, tags`. O campo `rules:` é a chave de
junção — `decisions --rule color.prohibition.black` traz todo julgamento anterior sobre a regra.

**Gatilho de promoção declarado: na terceira vez que uma regra é relaxada pelo mesmo motivo, isso
vira edição do `design-rules.json`, não um quarto ADR.** Sem esse gatilho, isto é um diário, não um
sistema que aprende.

### CLI

```
kunumi_critic.py rules      [--scope S] [--search Q] [--json]
kunumi_critic.py lint       PATH... [--scope S] [--render R.json] [--rule ID]
                                    [--severity-min violation] [--json]
kunumi_critic.py render     HTML [--canvas 1920x1080] [--scale 2] [--frame NAME]
                                 [--out-dir DIR] [--reduced-motion] [--json]
kunumi_critic.py review     HTML [--scope S] [--medium ...] [--out-dir DIR] [--json]
kunumi_critic.py emit       SPEC.json [--medium html --medium png --medium penpot]
kunumi_critic.py decisions  [--search Q] [--rule ID] [--status accepted] [--limit 10] [--json]
```

`rules` existe para o registry ser **inspecionável** — é assim que uma regra contestada é discutida
em vez de a ferramenta ser abandonada. `review` (= render + lint, imprimindo os caminhos exatos para
a passagem de visão) é o que a skill manda rodar em 95% dos casos.

**`main()` fica abaixo de ~120 linhas e só faz parsear, chamar uma função do pacote, e imprimir.**
Essa única restrição é o que mantém o caminho MCP aberto.

---

## Sequenciamento

| Fase | Conteúdo | Entregável que a prova |
|---|---|---|
| 1 | `findings.py`, `rules.py`, `design-rules.json`, `scan.py`, checks de cor/tipografia/geometria/artefato, `rules`+`lint`, testes + fixtures. **~15 regras** | Lint acha o `filter: brightness(0) invert(1)` e o leading 1.55 no CSS do próprio repo, com zero blocker falso |
| 2 | `pyproject.toml`+`uv.lock`, `render.py`, probe/degradação, `render`+`review`, checks medidos de logo | O par PNG fresco vs. defasado |
| 3 | **Skill `kosmos-designer`**: `SKILL.md`, `design-loop.md`, `critique-checklist.md`, `decisions/`, segundo symlink, `AGENTS.md`+README atualizados, `data-kunumi-*` no `template-preview.html`, regenerar os dois PNG | **Primeiro `create` de verdade**: briefing → HTML+PNG entregues com zero blocker, logado |
| 4 | `ArtifactSpec`, adaptadores html/png/penpot, `emit` | Um round-trip Penpot: plano → `execute_code` → `export_shape` → lint no export |
| 5 | CI, de-hardcodação do `validate-skills.py`, checks de copy e motion, ratchet de severidade | CI verde; `rules` citando autoridade ponta a ponta |

As fases 1 e 2 são pré-requisito do modo generativo: gerar sem verificação é a skill atual com mais
latência. A fase 3 é onde o `create` fica usável.

**Fronteira MCP, nomeada:** `scripts/kunumi_design/` **é** a futura superfície de tool;
`kunumi_critic.py` é casca fina de argparse. Quatro funções viram tool sem alteração —
`rules.effective_rules()` → `kunumi_rules`, `render.render_html()` → `kunumi_render`,
`checks.run()` → `kunumi_lint`, `adapters.emit()` → `kunumi_emit`. Cada uma já recebe entrada
serializável e devolve dataclass com `to_dict()`. Promover o loop a subagente precisa só de
`design-loop.md` → prompt + allowlist de tools; nenhum Python se move. **O que fecharia essa porta é
lógica de orquestração vazar para `main()`.**

## Verificação

**Experimento 1 — os PNG defasados e mal rotulados.** Sem artefato novo.
`kunumi_critic.py lint skills/kosmos-design-system/assets/web` deve produzir
`artifact.format-mismatch` (blocker: declara PNG, é JPEG com perda),
`artifact.stale` (violation: render anterior ao HTML e ao CSS que retrata) e
`artifact.unregistered` (advisory: fora de todo índice).

Depois `kunumi_critic.py render .../template-preview.html --canvas 1280x720` e pôr o render fresco ao
lado do commitado: o fresco mostra a headline **em caixa alta, em Space Grotesk**; o commitado mostra
caixa baixa em Figtree. **Esse par antes/depois é a prova de valor** — uma regressão visível que o
repo vem publicando, invisível a todo check existente.

**Experimento 2 — lint do `template-preview.html`, que é o conjunto de calibração.**

*Verdadeiros positivos esperados (em código commitado):* `logo.no-effects` blocker no
`filter: brightness(0) invert(1)`; `typography.line-height.display` violation no `1.55`.

*Controles negativos que **não** podem disparar* — cada um prova que um check é preciso e não
trigger-happy: `animation: background-drift 9s ... infinite` (9s está dentro da janela 6–12s);
`transform: scale(1.05)` (uniforme — prova que o check testa x≠y, não "tem scale");
`rgb(28 33 39 / 0.42)` e `color-mix(... var(--kunumi-gelo) 72% ...)` (provam a normalização de cor).

*Falsos positivos que o escopo tem de suprimir:* `body { background: #11151a }`, `box-shadow` e
`border-radius: 0.25rem` no `.stage` — tudo chrome de visualizador. Resolvido com
`data-kunumi-exempt="viewer-chrome"`, que é entregável da fase 3. O `#11151a` é o caso de juízo
interessante (near-Chumbo deliberado) → vira ADR 0002 de um jeito ou de outro.

**Experimento 3 — o primeiro `create`.** Briefing real ("seção hero para página do Instituto"),
loop completo de 9 passos, saída em HTML + PNG, zero blocker em ≤3 ciclos, com o ADR registrado.

**Testes.** `pytest` via `uv run pytest`, `tests/` na raiz; `conftest.py` insere o `scripts/` da
skill em `sys.path` (espelhando como os scripts são realmente invocados, já que o pacote nunca é
instalado). Fixtures **deliberadamente fora de norma, cada uma pareada com o conjunto exato de
rule-id que deve disparar, afirmado como igualdade de conjunto** — não `assert findings`, que é como
suíte de linter apodrece: `noncompliant-card.html`, `noncompliant-chart.html`,
`noncompliant-logo.html`, e **`compliant-card.html` que deve render zero blocker/violation** — o
teste mais importante da suíte. Mais `test_scopes.py` (as seis armadilhas como asserção),
`test_rules_derive.py` (mutar tokens em memória e afirmar que a regra acompanha — a guarda do
"derivar, não hardcodar"), `test_render.py` (`skipif(not probe().available)`), `test_findings.py`
(estabilidade do contrato JSON).

**CI** na fase 5: `.github/workflows/checks.yml` em PR e push, deixando o secret scan intacto —
`validate-skills.py`, `build_indices.py --check`, `pytest -q`, e o **ratchet**:
`kunumi_critic.py lint .../assets/web --severity-min blocker`, limiar que o repo passa depois de
corrigido o `filter` do logo. Apertar para `violation` depois é diff de uma palavra.

## Critério de "valor provado"

1. **Defeito real:** ≥5 findings genuínos em artefato já commitado, incluindo ≥1 que ninguém havia
   notado (previstos: o `filter` no logo e o leading 1.55)
2. **Precisão:** no conjunto de calibração, **zero** blocker ou violation que um humano julgue
   errado. Advisory é discutível; blocker nunca pode estar errado. **Medir isso como número — é o
   limiar de abandono**
3. **A visão paga a dependência:** ≥2 findings que o lint comprovadamente não produziria. Se a
   passagem de visão não achar nada além do lint, **cortar a dependência pesada** — esse é o
   critério de morte honesto
4. **O loop converge:** um artefato de briefing a entrega com zero blocker em ≤3 ciclos
5. **Precedente acumula:** ≥3 ADRs e ≥1 causando edição real do `design-rules.json`

## Riscos nomeados

- *Explosão de regras antes de precisão conquistada* → ship 15
- *Escopo usado como botão de mudo* → `rulesSkipped` em todo relatório + ADR obrigatório em todo
  relaxamento
- *Visão derivando para "achismo"* → checklist de perguntas fechadas com condição de falha
- *CSS varrido por regex é impreciso* → tirar comentários, rastrear aninhamento de
  `@media`/`@supports` para não ler bloco de reduced-motion como regra base, e limitar ambição:
  o que exige resolução real de cascata pertence à passagem de render/medição, não à estática
- *Duas skills competindo por gatilho* → descriptions de natureza distinta (ação vs. conhecimento)

> Nota de branch: este repo usa `main` com squash merge (`AGENTS.md`). A regra "branch a partir de
> `develop`" da memória vale para o Konstrukt, **não** para cá.
