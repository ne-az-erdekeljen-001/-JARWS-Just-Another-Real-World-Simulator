# JARWS Task-típus sémák — munkajavaslat

**Állapot:** nem kanonikus tervezet, emberi felülvizsgálatra. A mezők és szabályok javaslatok; egyik sem válik elfogadott projektdöntéssé ettől a dokumentumtól.

## Miért kell ez a következő lépés?

A meglévő prototípus két Task-típust nevez meg: `NORMAL_TASK` és `CORE_CHANGE`. A régi prototípus Checker-e csak a `None` eredményt utasítja el; az újabb csomag tesztsémái pedig egyszerű példák (`status="ok"`, illetve `change_summary`). Egyik sem teljes JARWS-szerződés.

A séma ellenőrizheti a kimenet alakját, az elfogadási feltételek lefedését és a bizonyítékokra hivatkozást. Önmagában nem bizonyítja, hogy egy szöveges vagy kreatív eredmény tartalmilag helyes. Az ilyen minőségi ítélethez külön emberi vagy megfelelően meghatározott ellenőrzés kell.

## Javasolt közös Task-bemenet

Mindkét típus használja a jelenlegi közös mezőket: `id`, `task_type`, `goal`, `input`, `constraints` és `provenance`. Az `input` javasolt kötelező részei:

| Mező | Javasolt típus | Ellenőrzés |
|---|---|---|
| `request` | nem üres szöveg | A konkrét kérést vagy műveletet írja le. |
| `acceptance_criteria` | legalább 1 elemű lista | Minden elemnek legyen stabil `criterion_id`, leírása és ellenőrzési módja. |

Az elfogadási feltétel ellenőrzési módjának javasolt értékei: `SCHEMA`, `TEST`, `EVIDENCE`, `HUMAN_REVIEW`. A Checker gépi ellenőrzésként az első három módhoz tartozó struktúrát és bizonyíték-hivatkozásokat tudja ellenőrizni; a `HUMAN_REVIEW` feltételt nem jelölheti önállóan elfogadottnak.

## `DOCUMENT_REVIEW` v0.1 bemenet és eredmény

Az első megvalósított munkafajta `NORMAL_TASK` alatt a `DOCUMENT_REVIEW`. A munkafajta bemenetének kötelező részei:

- `work_kind`: pontosan `DOCUMENT_REVIEW`;
- `request`: nem üres szöveg;
- `sources`: legalább egy `{ "source_id": "...", "reference": "..." }` elem, egyedi azonosítóval;
- `acceptance_criteria`: legalább egy `{ "criterion_id": "...", "description": "..." }` elem, egyedi azonosítóval.

Az eredmény kötelező alakja:

```json
{
  "schema_version": "0.1",
  "task_type": "NORMAL_TASK",
  "work_kind": "DOCUMENT_REVIEW",
  "outcome": "COMPLETED",
  "summary": "Rövid eredményösszefoglaló",
  "findings": [
    {
      "finding_id": "F-1",
      "category": "GAP",
      "statement": "A második forrás nem határozza meg az állapotátmenetet.",
      "source_refs": ["SRC-1", "SRC-2"]
    }
  ],
  "acceptance_checks": [
    {
      "criterion_id": "AC-1",
      "result": "PASS",
      "evidence_refs": ["SRC-1"]
    }
  ]
}
```

A `findings` lista lehet üres, ha a vizsgálat nem talált eltérést. Ha van megállapítás, legalább egy, a bemenetben felsorolt `source_id`-ra hivatkozzon. Minden elfogadási feltételhez pontosan egy `PASS` ellenőrzés kell, legalább egy, a Task bemenetében ismert `source_id`-val. Ismeretlen vagy ismételt azonosító, hiányzó kritérium, nem `COMPLETED` eredmény, illetve hibás forráshivatkozás elutasítandó.

**Korlát:** ezek az ellenőrzések az alakot, a hivatkozások létezését és a lefedettséget vizsgálják. Nem bizonyítják, hogy a megállapítások tartalmilag igazak vagy a források értelmezése helyes.

## `CORE_CHANGE`

Kísérleti v0.1 bemenetként a Validator megköveteli a nem üres `change_scope`-ot, az `impact_categories` listát, legalább egy `proposed_changes` elemet és legalább egy elfogadási feltételt. A kategóriák jelenlegi kódolása: `GOVERNANCE`, `PERMISSIONS`, `SECURITY`, `PROTECTED_ZONE`, `LIVE_SYSTEM_IMPACT`. Minden tervezett változtatás egyedi `change_id`, `target`, `action` és `rationale` mezőt kap. A `rollback_plan` jelenleg opcionális; kötelezővé tétele nyitott döntés.

Az eredmény kötelező mezői:

- `schema_version`, `task_type`, `outcome` és nem üres `summary`;
- `change_items`: pontosan fedje le a bemenetben tervezett változtatásokat; a `change_id`, `target` és `action` egyezzen a tervvel, az eredmény legyen `APPLIED`;
- minden change item `evidence_refs` mezője a Task bizonyítéklistájának már rögzített elemére hivatkozzon;
- `verification`: minden elfogadási feltételhez pontosan egy `PASS` elem és érvényes bizonyítékhivatkozás tartozzon.

Az `APPLIED` a Task által engedélyezett munkakörben elvégzett változtatást jelenti, és önmagában nem jelent éles aktiválást. A `CORE_CHANGE` külön Approval-rekordot igényel a már elfogadott munkakeret szerint. Az eredményséma nem helyettesíti az Approval-döntést, nem aktivál módosítást, és a Checker nem jogosult jóváhagyni vagy aktiválni.

## Tesztlefedettség

1. Mindkét típus érvényes kimenete `DONE`-hoz vezet a hozzá tartozó Approval-feltételek teljesülése esetén.
2. Hiányzó vagy hibás bemenetnél az Executor nem indul el.
3. `DOCUMENT_REVIEW` esetén minden elfogadási feltételhez pontosan egy ellenőrzés tartozik; minden forráshivatkozás ismert.
4. `CORE_CHANGE` esetén a kimenet nem térhet el a tervezett scope-tól; minden változtatáshoz és elfogadási feltételhez Task-bizonyíték kell.
5. `FAIL` eredmény, hiányzó bizonyítékhivatkozás és hibás séma-verzió elutasítandó.
6. Ellenőrizzük a JSON-kompatibilitást és a `python -O` alatti tesztfutást.

## Emberi döntést igénylő pontok

- A v0.1 követel-e további `DOCUMENT_REVIEW` kategóriákat, vagy elegendő az `AGREEMENT`, `GAP`, `CONTRADICTION`, `RISK`, `OPEN_QUESTION` készlet?
- Kell-e a források és megállapítások mellett külön fájl-/artefaktum-hivatkozás?
- A dokumentum tartalmi helyességének emberi felülvizsgálata mely későbbi komponenshez vagy folyamathoz tartozzon?
- Kötelező legyen-e a `CORE_CHANGE` típushoz rollback- vagy visszaállítási terv? Ez hatással lehet biztonságra és architektúrára, ezért külön döntést igényel.

**Státusz a próba során:** a felhasználó a `DOCUMENT_REVIEW`-t választotta első munkafajtának. A `DOCUMENT_REVIEW` és `CORE_CHANGE` fenti v0.1 sémáit most a különálló prototípus és annak tesztjei valósítják meg. Mindkettő kísérleti és nem kanonikus; a konkrét `CORE_CHANGE` scope-, bizonyíték- és rollback-szabályok felülvizsgálatra várnak.
