import pdfplumber
import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor
import time
import streamlit as st
from docx import Document


start = time.time()

@st.cache_resource
def load_skill_extractor():
    nlp = spacy.load("en_core_web_lg")
    return SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

skill_extractor = load_skill_extractor()

start = time.time()
def extract_pdf_data(file_path):
    data = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                data += text
    return data

def docx_to_text(file_path):
    doc = Document(file_path)
    print('from doc2docx import convert', doc)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def get_tokens(text):
    cleaned_text = (
        text.replace("\n", " ")
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("/", "")
        .replace("•", "")
        .replace("·", "")
    )

    return cleaned_text

def keyword_similarity(keyword1, keyword2):
    # Use spaCy to compute similarity between two keywords
    doc1 = skill_extractor.nlp(keyword1)
    doc2 = skill_extractor.nlp(keyword2)
    return doc1.similarity(doc2)

#put resume path here
def compare(resume_data, jd_data):
    resume_text = get_tokens(resume_data)

    resume_annotations = skill_extractor.annotate(resume_text)

    resume_skills = []
    for i in resume_annotations['results']['full_matches']:
        resume_skills.append(i['doc_node_value'])
    for i in resume_annotations['results']['ngram_scored']:
        resume_skills.append(i['doc_node_value'])
    resume_output = set(resume_skills)


    jd_text = get_tokens(jd_data)
    jd_annotations = skill_extractor.annotate(jd_text, tresh=1)
    jd_skills = []
    for i in jd_annotations['results']['full_matches']:
        jd_skills.append(i['doc_node_value'].lower())
    for i in jd_annotations['results']['ngram_scored']:
        jd_skills.append(i['doc_node_value'].lower())
    jd_output = set(jd_skills)


    matched_keywords = set()
    for jd_kw in jd_output:
            for resume_kw in resume_output:
                if keyword_similarity(jd_kw, resume_kw) >= 0.80:
                    matched_keywords.add(jd_kw)


    if len(matched_keywords) == 0:
        return 0
    else:
        percentage = (len(matched_keywords)/len(jd_output))*100
        return percentage

tab1, tab2 = st.tabs(["**Home**", "**Results**"])

with tab1:
    st.title("Resume Scoring System")
    uploaded_files = st.file_uploader(
        '**Choose your resume.pdf file:** ', type=["pdf", "doc", "docx"], accept_multiple_files=True)
    JD_file = st.file_uploader(
        '**Choose your Job Description.pdf file:** ', type="pdf")
    comp_pressed = st.button("Compare", disabled=uploaded_files is None or JD_file is None)

    if comp_pressed and uploaded_files and JD_file:
        with st.spinner('Comparing resumes with job description...'):
            uploaded_file_paths = []
            JD = extract_pdf_data(JD_file)
            for file in uploaded_files:
                if file.name.endswith(".pdf") or file.name.endswith(".PDF"):
                    uploaded_file_paths.append(extract_pdf_data(file))
                elif file.name.endswith(".docx") or file.name.endswith(".DOCX"):
                    uploaded_file_paths.append(docx_to_text(file))
            score_list = [compare(resume, JD) for resume in uploaded_file_paths]

with tab2:
    st.header("Results")
    my_dict = {}
    if comp_pressed and uploaded_files:
        for i in range(len(score_list)):
            my_dict[uploaded_files[i].name] = score_list[i]
        sorted_dict = dict(sorted(my_dict.items()))
        for idx, (file_name, score_val) in enumerate(sorted_dict.items()):
                st.markdown(
                f"**{idx + 1}.** {file_name} - **Score:** {score_val:.2f}",
                unsafe_allow_html=True
            )

end = time.time()
print('total time', end-start)