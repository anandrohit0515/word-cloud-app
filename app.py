import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import fitz  # PyMuPDF for PDF text extraction
import numpy as np
from PIL import Image
import io
import os
import pandas as pd

# ------------------ Page Configuration ------------------
st.set_page_config(page_title="Word Cloud Generator", layout="wide")
st.title("🌥️ Word Cloud Generator")

# ========================================================
# 🎨 SIDEBAR: DESIGN OPTIONS
# ========================================================

st.sidebar.header("🎨 Design Options")

# Background color picker
bg_color = st.sidebar.color_picker("Background Color", "#ffffff")

# Sliders for word cloud size and content control
max_words = st.sidebar.slider("Max Words", 50, 300, 200, 10)
width = st.sidebar.slider("Image Width", 400, 1200, 800, 100)
height = st.sidebar.slider("Image Height", 300, 800, 400, 100)

# Predefined color maps from matplotlib
colormap = st.sidebar.selectbox("Color Scheme", [
    "viridis", "plasma", "inferno", "magma", "cividis",
    "cool", "hot", "spring", "summer", "autumn", "winter"
])

# Font selection from the "fonts" directory
font_files = [f for f in os.listdir("fonts") if f.endswith(".ttf")]
font_choice = st.sidebar.selectbox("Font", ["Default"] + font_files)
font_path = os.path.join("fonts", font_choice) if font_choice != "Default" else None

# Mask shape selection
shape = st.sidebar.selectbox("Built-in Shape", ["None", "Circle", "Heart"])

# Option to upload a custom mask image
uploaded_mask = st.sidebar.file_uploader("Or upload custom mask (PNG)", type=["png"])

# ========================================================
# 🔍 MASK LOADING FUNCTION
# ========================================================

def load_mask():
    """Loads a mask from uploaded file or built-in selection."""
    if uploaded_mask:
        return np.array(Image.open(uploaded_mask).convert("L"))  # convert to grayscale mask
    elif shape != "None":
        path = f"masks/{shape.lower()}.png"
        return np.array(Image.open(path))
    else:
        return None

# ========================================================
# 📄 INPUT SOURCE: TEXT OR PDF
# ========================================================

st.sidebar.header("📄 Input Source")
input_method = st.sidebar.radio("Choose:", ["Text", "PDF Upload"])

text_input = ""

# User inputs text manually
if input_method == "Text":
    text_input = st.text_area("Enter your text below:", height=200)

# User uploads a PDF file
elif input_method == "PDF Upload":
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_pdf is not None:
        # Extract text from all pages using PyMuPDF
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        pdf_text = "".join([page.get_text() for page in doc])
        text_input = pdf_text
        st.success("PDF text extracted successfully.")
        st.text_area("Extracted Text:", value=pdf_text, height=200)

# ========================================================
# 🚀 WORD CLOUD GENERATION
# ========================================================

if st.button("Generate Word Cloud") and text_input.strip():
    # Load the appropriate mask
    mask = load_mask()

    # Create word cloud with selected parameters
    wc = WordCloud(
        width=width,
        height=height,
        background_color=bg_color,
        max_words=max_words,
        colormap=colormap,
        mask=mask,
        font_path=font_path or None
    ).generate(text_input)

    # ------------------ Display Word Cloud ------------------
    fig, ax = plt.subplots(figsize=(width/100, height/100))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    # ------------------ Download Word Cloud as PNG ------------------
    buf = io.BytesIO()
    wc.to_image().save(buf, format='PNG')
    st.download_button(
        label="📥 Download Word Cloud as PNG",
        data=buf.getvalue(),
        file_name="word_cloud.png",
        mime="image/png"
    )

    # ------------------ Show Word Frequency Table + Chart ------------------
    st.subheader("📊 Word Frequency Table")

    # Get normalized frequencies and raw counts
    normalized_freqs = wc.words_  # {'word': 1.0, ...}
    raw_counts = wc.process_text(text_input)  # {'word': 123, ...}

    # Merge raw count + normalized frequency
    freq_data = [
        {
            "Word": word,
            "Raw Count": raw_counts.get(word, 0),
            "Normalized Frequency (%)": round(freq * 100, 2)
        }
        for word, freq in normalized_freqs.items()
    ]

    # Sort by raw count (descending) and keep top 10
    freq_data = sorted(freq_data, key=lambda x: x["Raw Count"], reverse=True)[:10]

    # Split into 2 columns: table on left, bar chart on right
    left_col, right_col = st.columns([2, 3])

    with left_col:
        # Display table
        st.dataframe(freq_data, use_container_width=False)

        # CSV Export
        df_export = pd.DataFrame(freq_data)
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name="word_frequencies.csv",
            mime="text/csv"
        )

    with right_col:
        # Subheader for the chart
        st.markdown("**📈 Top 10 Words (Bar Chart)**")

        # Convert to DataFrame
        df_bar = pd.DataFrame(freq_data)

        # Set consistent chart height (approx. matches 10-row table height)
        fig_bar, ax_bar = plt.subplots(figsize=(5, 4.5))  # width=5in, height=4.5in

        # Plot horizontal bar chart
        ax_bar.barh(df_bar["Word"], df_bar["Raw Count"], color="skyblue")
        ax_bar.invert_yaxis()  # Highest count on top
        ax_bar.set_xlabel("Raw Count")
        ax_bar.set_title("Top 10 Words")
        # Show chart
        st.pyplot(fig_bar)
