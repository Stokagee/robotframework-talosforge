Často kladené dotazy
====================

.. _faq-example:

Proč je pole ``example`` ignorováno?
------------------------------------

Pole ``example`` (jednotné číslo) v OpenAPI specifikacích obsahuje pouze jednu hodnotu.
Pokud bychom ji používali, všechna generovaná data by byla stejná - to je pro testovací
data špatně.

TalosForge je určen pro generování **různorodých** testovacích dat.

Pokud potřebujete konkrétní hodnoty:
- Použijte ``examples`` (množné číslo) s více hodnotami
- Použijte ``enum`` pro validační omezení
- Nebo přijměte náhodné hodnoty od Fakeru

.. seealso:: :doc:`zmeny_chovani`
