# Migrace z verze 0.2.x na 0.3.0

Tento dokument vás provede změnami mezi verzemi 0.2.x a 0.3.0.

## Co se změnilo?

Pole `"example"` (jednotné číslo) v OpenAPI schématech je **nyní ignorováno**.

### Předchozí chování (0.2.x)

```json
{"type": "string", "example": "Jan Novák"}
```

Vždy vrátilo: `"Jan Novák"` (statická hodnota)

### Nové chování (0.3.0)

```json
{"type": "string", "example": "Jan Novák"}
```

Vrací: Náhodná česká jména z Fakeru (`"Petr Svoboda"`, `"Jana Dvořáková"`, ...)

### Proč tato změna?

Statické hodnoty z `"example"` pole byly proti původnímu účelu knihovny -
generovat **různorodá** testovací data. Deterministické chování zhoršovalo
pokrytí testovacích scénářů.

---

## Jak migrovat?

### Možnost 1: Použijte `"examples"` (množné číslo)

Pokud potřebujete vybírat z konkrétních hodnot:

**Před:**
```json
{"name": {"type": "string", "example": "Jan Novák"}}
```

**Po:**
```json
{"name": {"type": "string", "examples": ["Jan Novák", "Petr Svoboda", "Jana Dvořáková"]}}
```

Výsledek: Náhodný výběr ze seznamu (řádově stejně jako dříve, ale s více hodnotami)

---

### Možnost 2: Použijte `"enum"` pro validační omezení

Pokud jsou hodnoty validační constraint:

```json
{"status": {"type": "string", "enum": ["active", "inactive", "pending"]}}
```

Výsledek: Náhodný výběr z enum (nejvyšší priorita v systému)

---

### Možnost 3: Nechte Faker generovat (DOPORUČENO)

Odstraňte `"example"` a nechte Faker generovat různorodá data:

**Před:**
```json
{"email": {"type": "string", "format": "email", "example": "test@example.com"}}
```

**Po:**
```json
{"email": {"type": "string", "format": "email"}}
```

Výsledek: Náhodné validní emaily (`"jan.novak@example.cz"`, `"petr.svoboda@test.org"`, ...)

---

## Aktualizace testů

### Testy ověřující konkrétní `"example"` hodnoty

**Před (selže v 0.3.0):**
```python
data = generate({"name": {"type": "string", "example": "Jan Novák"}})
assert data["name"] == "Jan Novák"  # ❌ Nyní selže
```

**Po:**
```python
# Možnost A: Ověřte pouze typ
data = generate({"name": {"type": "string"}})
assert isinstance(data["name"], str)  # ✓

# Možnost B: Použijte "examples"
data = generate({"name": {"type": "string", "examples": ["Jan Novák"]}})
assert data["name"] == "Jan Novák"  # ✓

# Možnost C: Ověřte formát
data = generate({"name": {"type": "string", "example": "Jan Novák"}})
assert " " in data["name"]  # ✓ Jméno obsahuje mezeru
```

---

## Často kladené dotazy

### Rozbíjí to mé existující testy?

Pokud jste se **spoléhali** na statické hodnoty z `"example"`, ano.
Pokud jste používali `"examples"` (plurál) nebo `"enum"`, ne.

### Můžu vrátit staré chování?

Ne. Staré chování bylo chybné a proti účelu knihovny.
Použijte `"examples"` (množné číslo) pro seznam hodnot.

### Co když chci deterministické testy?

Použijte `"examples"` s jednou hodnotou:
```json
{"value": {"type": "integer", "examples": [42]}}
```
Toto vždy vrátí `42`.

### Co s OpenAPI specifikacemi?

OpenAPI specifikace často obsahují `"example"` pole.
TalosForge je nyní ignoruje a generuje různorodá data.
Toto je správné chování pro **testovací data**.

---

## Kontrolní seznam migrace

- [ ] Přečtěte si novou sekci "Priorita zpracování schématu" v README.md
- [ ] Najděte všechna `"example"` pole ve vašich schématech
- [ ] Rozhodněte: ponechat (ignorováno) → změnit na `"examples"` → odstranit
- [ ] Aktualizujte testy spoléhající na konkrétní `"example"` hodnoty
- [ ] Spusťte testy a ověřte chování
- [ ] V případě problémů se podívejte do FAQ

---

## Potřebujete pomoc?

- Otevřete issue na GitHubu
- Podívejte se do [FAQ](docs/faq.rst)
- Kontaktujte maintainera
