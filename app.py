import streamlit as st
import pypdf
from openai import OpenAI

# --- KONFIGURACJA STRONY ---
# Używamy szerokiego układu, żeby wyglądało to jak prawdziwy dashboard
st.set_page_config(page_title="MeriTor - Panel Studenta", page_icon="🎓", layout="wide")

# --- PANEL BOCZNY (Nawigacja i Profil) ---
st.sidebar.title("🎓 MeriTor")
st.sidebar.markdown("---")
# Widmo profilu studenta (Logowanie)
st.sidebar.success("👤 **Zalogowano:** Wojciech Pietrzak")
st.sidebar.caption("Nr albumu: 123456 | Informatyka (AI) II st.")
st.sidebar.markdown("---")

# Wybór przedmiotu
st.sidebar.subheader("📚 Twoje Przedmioty")
przedmiot = st.sidebar.radio(
    "Wybierz moduł:",
    ["Fizyka / Podstawy Kwantowe", "Sztuczna Inteligencja", "Algorytmy i Struktury", "Bazy Danych"]
)

st.sidebar.markdown("---")
st.sidebar.caption("⚙️ Konfiguracja MVP:")
api_key = st.sidebar.text_input("Klucz API (Groq):", type="password")

# --- GŁÓWNY DASHBOARD ---
st.title(f"📖 Przedmiot: {przedmiot}")
st.markdown("Witaj w swoim pulpicie. MeriTor przeanalizował już pliki od wykładowcy. Możesz zadać pytanie lub wgrać własne notatki, aby bot uwzględnił je w odpowiedziach.")
st.divider()

# Podział na dwie kolumny: Lewa (Pliki), Prawa (Czat AI)
col1, col2 = st.columns([1, 2], gap="large")

pdf_text = ""

with col1:
    st.subheader("📂 Baza Wiedzy Przedmiotu")
    
    # Pliki wykładowcy (Widmo - zablokowane)
    st.markdown("##### 🔒 Materiały od Wykładowcy (Tylko odczyt)")
    st.info("📄 `[1] Wykład_1_Wprowadzenie.pdf`\n\n📄 `[2] Sylabus_2026.pdf`\n\n📄 `[3] Kubit_Fizyczny_Romaniuk.pdf`")
    st.caption("Powyższe pliki zostały automatycznie zaindeksowane w wektorowej bazie danych Merito.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Własne notatki studenta
    st.markdown("##### 📝 Twoje Notatki (Rozszerzenie bazy)")
    uploaded_file = st.file_uploader("Dodaj plik z notatkami (PDF), aby MeriTor mógł się do nich odnosić:", type="pdf")
    
    if uploaded_file:
        with st.spinner("Indeksowanie Twoich notatek..."):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                pdf_text += page.extract_text() + "\n"
            st.success("✅ Notatki dodane do kontekstu bota!")

with col2:
    st.subheader("🤖 Asystent MeriTor")
    
    # --- INTERFEJS CZATU ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Ograniczenie wysokości czatu, żeby ładnie wyglądało
    chat_container = st.container(height=400)
    
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # Logika działania AI
    if user_query := st.chat_input(f"Zadaj pytanie z przedmiotu: {przedmiot}..."):
        if not api_key:
            st.error("Wprowadź klucz API w lewym panelu, aby uruchomić bota!")
        else:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with chat_container.chat_message("user"):
                st.markdown(user_query)

            with chat_container.chat_message("assistant"):
                with st.spinner("MeriTor przeszukuje materiały z zajęć..."):
                    try:
                        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                        
                        # System prompt z obsługą wgranych notatek
                        system_prompt = f"""
                        Jesteś MeriTor, oficjalnym asystentem dydaktycznym na Uniwersytecie WSB Merito.
                        Odpowiadasz na pytania z przedmiotu: {przedmiot}.
                        Jeśli student wgrał notatki, znajdują się one tutaj: {pdf_text[:15000]}
                        Opieraj się na zweryfikowanej wiedzy akademickiej. Bądź zwięzły, profesjonalny i pomocny.
                        """
                        
                        response = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_query}
                            ],
                            temperature=0.1
                        )
                        
                        answer = response.choices[0].message.content
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"Błąd połączenia: {e}")