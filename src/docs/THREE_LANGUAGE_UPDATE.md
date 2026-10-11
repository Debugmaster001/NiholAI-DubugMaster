# Nihol AI — UZ / EN / RU update

- Public `/demo/` includes UZ / EN / RU controls, translated labels, screening verdicts, evidence rule titles, and PDF headings.
- Language preference is saved in browser localStorage, not sent to third parties.
- Rule identifiers (S01–S12 / G01–G09) and policy version are unchanged. The same analysis engine evaluates all languages.
- PDF text is localized using a `lang` field from the request. Original source quotations remain unchanged for auditability.
- Preliminary screening does **not** constitute an official taxonomy certification or loan approval.
- Some inherited dashboard pages have existing Django locale catalogs; this patch specifically completes the public demo and its report. It is not a claim of complete site-wide translation.
- To deploy safely, upload changes to a new `feature/three-languages` branch, verify in staging, then merge to main.
