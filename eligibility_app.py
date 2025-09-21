
import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import os

st.set_page_config(page_title="DMT Eligibility: Lecanemab & Donanemab", page_icon="🧠", layout="wide")

REG_PATH = os.environ.get("REGISTRO_DMT_PATH", "registro_dmt.csv")

def compute_eligibility(eta, diagnosi, mmse, cdr_global, amiloide_pos, caregiver,
                        microemorragie_n, siderosi, lesioni_isch, fazekas,
                        anticoagulanti, ictus12m, neoplasia, autoimmuni, insuff_organo,
                        apoe_eseguito, apoe_genotipo):
    inclusione = {
        "dx_ok": diagnosi in {"MCI prodromico di Alzheimer", "Malattia di Alzheimer lieve"},
        "mmse_ok": mmse >= 20,
        "cdr_ok": cdr_global in {0.5, 1},
        "amiloide_ok": (amiloide_pos == "Sì"),
        "caregiver_ok": (caregiver == "Sì"),
    }
    eta_ok_lec = 50 <= eta <= 85
    eta_ok_don = 60 <= eta <= 85
    esclusioni = {
        "anticoagulanti_no": (anticoagulanti == "No"),
        "microemorragie_ok": (microemorragie_n <= 4),
        "siderosi_no": (siderosi == "No"),
        "ictus_recenti_no": (ictus12m == "No"),
        "neoplasia_no": (neoplasia == "No"),
        "autoimmuni_no": (autoimmuni == "No"),
        "organi_ok": (insuff_organo == "No"),
    }
    base_ok = all(inclusione.values()) and all(esclusioni.values())
    elig_lec = base_ok and eta_ok_lec
    elig_don = base_ok and eta_ok_don
    apoe_e4 = False
    if apoe_eseguito == "Sì" and apoe_genotipo:
        apoe_e4 = apoe_genotipo in {"ε2/ε4","ε3/ε4","ε4/ε4"}
    aria_risk = apoe_e4 or (microemorragie_n >= 1)
    label = {
        "dx_ok": "Diagnosi non ammessa (serve MCI prodromico o AD lieve)",
        "mmse_ok": "MMSE < 20",
        "cdr_ok": "CDR Global non 0.5–1",
        "amiloide_ok": "Amiloide non confermato",
        "caregiver_ok": "Caregiver non disponibile",
        "anticoagulanti_no": "Anticoagulanti orali in corso",
        "microemorragie_ok": "> 4 microemorragie",
        "siderosi_no": "Siderosi corticale presente",
        "ictus_recenti_no": "Ictus/TIA negli ultimi 12 mesi",
        "neoplasia_no": "Neoplasia attiva",
        "autoimmuni_no": "Malattie autoimmuni attive / immunosoppressione",
        "organi_ok": "Insufficienza d’organo grave (cardio/rene/fegato)",
    }
    motivi = [label[k] for k, v in {**inclusione, **esclusioni}.items() if not v]

    # DMT consigliata
    if elig_lec and elig_don:
        dmt_consigliata = "Entrambe (valutare preferenze, logistica, rischio ARIA)"
    elif elig_lec and not elig_don:
        dmt_consigliata = "Lecanemab"
    elif elig_don and not elig_lec:
        dmt_consigliata = "Donanemab"
    else:
        dmt_consigliata = "Nessuna (vedi motivi)"
    return elig_lec, elig_don, aria_risk, apoe_e4, motivi, dmt_consigliata

def ensure_registry():
    if not os.path.exists(REG_PATH):
        cols = ["timestamp","id_paziente","eta","diagnosi","mmse","cdr_global","amiloide_pos","caregiver",
                "microemorragie_n","siderosi","lesioni_isch_gt2cm","fazekas","anticoagulanti",
                "ictus12m","neoplasia_attiva","autoimmuni_attive","insuff_organo_grave",
                "apoe_eseguito","apoe_genotipo","eligibile_lecanemab","eligibile_donanemab",
                "rischio_ARIA_alto","apoe_e4","dmt_consigliata","motivi_non_eligibilita"]
        pd.DataFrame(columns=cols).to_csv(REG_PATH, index=False, encoding="utf-8-sig")

def load_registry():
    ensure_registry()
    return pd.read_csv(REG_PATH)

def append_registry(row):
    ensure_registry()
    df = pd.read_csv(REG_PATH)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(REG_PATH, index=False, encoding="utf-8-sig")

tab1, tab2 = st.tabs(["🧪 Valutazione singolo paziente", "📊 Report & Registro"])

with tab1:
    st.title("🧪 Valutazione singolo paziente")
    colA, colB = st.columns([2,1])
    with colA:
        st.subheader("1) Dati clinici")
        c1, c2 = st.columns(2)
        with c1:
            id_paz = st.text_input("ID paziente (anonimizzato)", value="")
            eta = st.number_input("Età (anni)", min_value=18, max_value=120, value=72, step=1)
            diagnosi = st.selectbox("Diagnosi", ["MCI prodromico di Alzheimer", "Malattia di Alzheimer lieve", "Altro"])
            mmse = st.number_input("MMSE", min_value=0, max_value=30, value=25, step=1)
        with c2:
            cdr_global = st.selectbox("CDR Global", [0, 0.5, 1, 2, 3], index=2)
            amiloide_pos = st.selectbox("Biomarcatori amiloide positivi?", ["No", "Sì"], index=1)
            caregiver = st.selectbox("Caregiver disponibile?", ["No", "Sì"], index=1)

        st.subheader("2) Imaging RM e rischio emorragico")
        c3, c4 = st.columns(2)
        with c3:
            microemorragie_n = st.number_input("Numero microemorragie", min_value=0, max_value=99, value=0, step=1)
            siderosi = st.selectbox("Siderosi corticale presente?", ["No", "Sì"], index=0)
        with c4:
            lesioni_isch = st.selectbox("Lesioni ischemiche > 2 cm?", ["No", "Sì"], index=0)
            fazekas = st.selectbox("Leucoaraiosi (Fazekas)", [0,1,2,3], index=0)

        st.subheader("3) Comorbidità e terapie")
        c5, c6 = st.columns(2)
        with c5:
            anticoagulanti = st.selectbox("Anticoagulanti orali in corso?", ["No", "Sì"], index=0)
            ictus12m = st.selectbox("Ictus/TIA negli ultimi 12 mesi?", ["No", "Sì"], index=0)
            neoplasia = st.selectbox("Neoplasia attiva?", ["No", "Sì"], index=0)
        with c6:
            autoimmuni = st.selectbox("Malattie autoimmuni attive / immunosoppressione?", ["No", "Sì"], index=0)
            insuff_organo = st.selectbox("Insufficienza d'organo grave (cardio/rene/fegato)?", ["No", "Sì"], index=0)

        st.subheader("4) Genotipo ApoE (opzionale)")
        apoe_eseguito = st.selectbox("Test ApoE eseguito?", ["No", "Sì"], index=0)
        apoe_genotipo = None
        if apoe_eseguito == "Sì":
            apoe_genotipo = st.selectbox("Genotipo ApoE", ["ε2/ε2","ε2/ε3","ε3/ε3","ε2/ε4","ε3/ε4","ε4/ε4"], index=2)

        if st.button("Calcola eleggibilità", use_container_width=True):
            elig_lec, elig_don, aria_risk, apoe_e4, motivi, dmt_consigliata = compute_eligibility(
                eta, diagnosi, mmse, cdr_global, amiloide_pos, caregiver,
                microemorragie_n, siderosi, lesioni_isch, fazekas,
                anticoagulanti, ictus12m, neoplasia, autoimmuni, insuff_organo,
                apoe_eseguito, apoe_genotipo
            )
            with colB:
                st.subheader("Risultati")
                st.metric("Lecanemab", "✅ Eleggibile" if elig_lec else "❌ Non eleggibile")
                st.metric("Donanemab", "✅ Eleggibile" if elig_don else "❌ Non eleggibile")
                st.metric("Rischio ARIA", "⚠️ Alto" if aria_risk else "Basso")
                st.success(f"DMT consigliata: **{dmt_consigliata}**")

            if motivi:
                st.error("\\n".join(f"• {m}" for m in motivi))

            if apoe_e4:
                st.info("ApoE ε4 rilevato → considerare counselling sul rischio ARIA e monitoraggio RM.")

            payload = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "id_paziente": id_paz,
                "eta": eta,
                "diagnosi": diagnosi,
                "mmse": mmse,
                "cdr_global": cdr_global,
                "amiloide_pos": amiloide_pos,
                "caregiver": caregiver,
                "microemorragie_n": microemorragie_n,
                "siderosi": siderosi,
                "lesioni_isch_gt2cm": lesioni_isch,
                "fazekas": fazekas,
                "anticoagulanti": anticoagulanti,
                "ictus12m": ictus12m,
                "neoplasia_attiva": neoplasia,
                "autoimmuni_attive": autoimmuni,
                "insuff_organo_grave": insuff_organo,
                "apoe_eseguito": apoe_eseguito,
                "apoe_genotipo": apoe_genotipo or "",
                "eligibile_lecanemab": int(elig_lec),
                "eligibile_donanemab": int(elig_don),
                "rischio_ARIA_alto": int(aria_risk),
                "apoe_e4": int(apoe_e4),
                "dmt_consigliata": dmt_consigliata,
                "motivi_non_eligibilita": "; ".join(motivi)
            }

            csave1, csave2 = st.columns(2)
            with csave1:
                if st.button("💾 Salva su registro locale", use_container_width=True):
                    append_registry(payload)
                    st.success("Salvato nel registro locale.")
            with csave2:
                csv_one = pd.DataFrame([payload]).to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ Scarica riga paziente (CSV)", data=csv_one,
                                   file_name="valutazione_dmt_paziente.csv", mime="text/csv", use_container_width=True)

with tab2:
    st.title("📊 Report & Registro pazienti")
    df = load_registry()
    st.caption(f"Percorso registro: `{REG_PATH}`")

    if df.empty:
        st.info("Il registro è vuoto. Aggiungi pazienti dalla scheda 'Valutazione singolo paziente'.")
    else:
        # Filtri
        with st.expander("Filtri", expanded=True):
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                elig_lec_f = st.selectbox("Lecanemab", ["Tutti","Eleggibile","Non eleggibile"], index=0)
            with c2:
                elig_don_f = st.selectbox("Donanemab", ["Tutti","Eleggibile","Non eleggibile"], index=0)
            with c3:
                aria_f = st.selectbox("Rischio ARIA", ["Tutti","Alto","Basso"], index=0)
            with c4:
                dx_f = st.multiselect("Diagnosi", sorted(df["diagnosi"].dropna().unique().tolist() or []))
            with c5:
                text_f = st.text_input("Ricerca testo (ID/motivi)", value="")

        fdf = df.copy()
        if elig_lec_f != "Tutti":
            fdf = fdf[fdf["eligibile_lecanemab"] == (1 if elig_lec_f=="Eleggibile" else 0)]
        if elig_don_f != "Tutti":
            fdf = fdf[fdf["eligibile_donanemab"] == (1 if elig_don_f=="Eleggibile" else 0)]
        if aria_f != "Tutti":
            fdf = fdf[fdf["rischio_ARIA_alto"] == (1 if aria_f=="Alto" else 0)]
        if dx_f:
            fdf = fdf[fdf["diagnosi"].isin(dx_f)]
        if text_f:
            m = fdf.apply(lambda r: text_f.lower() in (str(r["id_paziente"])+" "+str(r["motivi_non_eligibilita"])).lower(), axis=1)
            fdf = fdf[m]

        # KPI
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Totale pazienti", len(fdf))
        k2.metric("Eleggibili Lecanemab", int((fdf["eligibile_lecanemab"]==1).sum()))
        k3.metric("Eleggibili Donanemab", int((fdf["eligibile_donanemab"]==1).sum()))
        k4.metric("Rischio ARIA alto", int((fdf["rischio_ARIA_alto"]==1).sum()))

        st.dataframe(fdf, use_container_width=True, height=420)

        # Export
        cexp1, cexp2 = st.columns(2)
        with cexp1:
            st.download_button("⬇️ Esporta vista filtrata (CSV)",
                               data=fdf.to_csv(index=False).encode("utf-8-sig"),
                               file_name="registro_filtrato.csv", mime="text/csv", use_container_width=True)
        with cexp2:
            st.download_button("⬇️ Esporta registro completo (CSV)",
                               data=df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="registro_completo.csv", mime="text/csv", use_container_width=True)

st.divider()
st.caption("© 2025 – Uso clinico interno. Verificare criteri locali (AIFA/EMA) e aggiornare la logica se necessario. Variabile d'ambiente REGISTRO_DMT_PATH per percorso registro.")
