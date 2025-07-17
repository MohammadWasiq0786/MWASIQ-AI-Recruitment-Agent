
import re
import PyPDF2
import io
import json
import tempfile
import os

from euriai import EuriaiEmbeddings, EuriaiLangChainLLM
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter

from concurrent.futures import ThreadPoolExecutor


class ResumeAnalysisAgent:
    def __init__(self, api_key, cutoff_score=75):
        self.api_key = api_key
        self.cutoff_score = cutoff_score
        self.resume_text = None
        self.rag_vectorstore = None
        self.analysis_result = None
        self.jd_text = None
        self.extracted_skills = None
        self.resume_weaknesses = []
        self.resume_strengths = []
        self.improvement_suggestions = {}
        self._temp_files = []

    def _register_temp_file(self, path):
        self._temp_files.append(path)

    def _normalize_response(self, response):
        """Ensure response is a clean string."""
        if isinstance(response, dict):
            for key in ('text', 'content', 'answer', 'result'):
                if key in response:
                    return str(response[key])
            return json.dumps(response)
        if hasattr(response, 'content'):
            return str(response.content)
        return str(response)

    def extract_text_from_pdf(self, pdf_file):
        try:
            if hasattr(pdf_file, 'getvalue'):
                pdf_data = pdf_file.getvalue()
                pdf_file_like = io.BytesIO(pdf_data)
                reader = PyPDF2.PdfReader(pdf_file_like)
            else:
                reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_txt(self, txt_file):
        try:
            if hasattr(txt_file, 'getvalue'):
                return txt_file.getvalue().decode('utf-8')
            else:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error extracting text from TXT: {e}")
            return ""

    def extract_text_from_file(self, file):
        ext = file.name.split('.')[-1].lower() if hasattr(file, 'name') else file.split('.')[-1].lower()
        if ext == 'pdf':
            return self.extract_text_from_pdf(file)
        elif ext == 'txt':
            return self.extract_text_from_txt(file)
        else:
            print(f"Unsupported file type: {ext}")
            return ""

    def create_rag_vector_store(self, text):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
        chunks = splitter.split_text(text)
        embeddings = EuriaiEmbeddings(api_key=self.api_key)
        return FAISS.from_texts(chunks, embeddings)

    def create_vector_store(self, text):
        embeddings = EuriaiEmbeddings(api_key=self.api_key)
        return FAISS.from_texts([text], embeddings)

    def analyze_skill(self, qa_chain, skill):
        query = f"Rate proficiency in {skill} (0-10) and explain."
        response = qa_chain.invoke(query)
        text = self._normalize_response(response)
        score_match = re.search(r"(\d{1,2})", text)
        score = int(score_match.group(1)) if score_match else 0
        reasoning = text.split('.', 1)[1].strip() if '.' in text else ""
        return skill, min(score, 10), reasoning

    def semantic_skill_analysis(self, resume_text, skills):
        vectorstore = self.create_vector_store(resume_text)
        retriever = vectorstore.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm=EuriaiLangChainLLM(api_key=self.api_key, model="gpt-4.1-nano", temperature=0.7, max_tokens=300),
            retriever=retriever,
            return_source_documents=False
        )
        skill_scores = {}
        skill_reasoning = {}
        missing_skills = []
        total_score = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda skill: self.analyze_skill(qa_chain, skill), skills))

        for skill, score, reasoning in results:
            skill_scores[skill] = score
            skill_reasoning[skill] = reasoning
            total_score += score
            if score <= 5:
                missing_skills.append(skill)

        overall_score = int((total_score / (10 * len(skills))) * 100)
        strengths = [s for s, sc in skill_scores.items() if sc >= 7]
        self.resume_strengths = strengths
        return {
            "overall_score": overall_score,
            "skill_scores": skill_scores,
            "skill_reasoning": skill_reasoning,
            "selected": overall_score >= self.cutoff_score,
            "missing_skills": missing_skills,
            "strengths": strengths
        }

    def analyze_resume(self, resume_file, role_requirements=None, custom_jd=None):
        self.resume_text = self.extract_text_from_file(resume_file)
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8').name
        with open(tmp_path, 'w', encoding='utf-8') as tmp:
            tmp.write(self.resume_text)
        self._register_temp_file(tmp_path)
        self.rag_vectorstore = self.create_rag_vector_store(self.resume_text)

        if custom_jd:
            self.jd_text = self.extract_text_from_file(custom_jd)
            self.extracted_skills = self.extract_skills_from_jd(self.jd_text)
            self.analysis_result = self.semantic_skill_analysis(self.resume_text, self.extracted_skills)
        elif role_requirements:
            self.extracted_skills = role_requirements
            self.analysis_result = self.semantic_skill_analysis(self.resume_text, role_requirements)

        return self.analysis_result

    def ask_question(self, question):
        if not self.rag_vectorstore:
            return "No resume analyzed yet."
        retriever = self.rag_vectorstore.as_retriever(search_kwargs={"k": 3})
        qa_chain = RetrievalQA.from_chain_type(
            llm=EuriaiLangChainLLM(api_key=self.api_key, model="gpt-4.1-nano", temperature=0.7, max_tokens=300),
            retriever=retriever,
            return_source_documents=False
        )
        response = qa_chain.invoke(question)
        return self._normalize_response(response)

    # Stub methods to avoid attribute errors

    
    def ask_question(self, question):
        """Ask a question about the resume"""
        if not self.rag_vectorstore or not self.resume_text:
            return "Please analyze a resume first."
        
        retriever = self.rag_vectorstore.as_retriever(
            search_kwargs={"k": 3}  
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=EuriaiLangChainLLM(api_key=self.api_key, model="gpt-4.1-nano", temperature=0.6, max_tokens=400),
            # ChatOpenAI(model="gpt-4o", api_key=self.api_key),
            chain_type="stuff",  
            retriever=retriever,
            return_source_documents=False,
        )
        
        raw_response = qa_chain.invoke(question)
        if isinstance(raw_response, list):
            combined = ''.join(r.get('text', '') if isinstance(r, dict) else str(r) for r in raw_response)
        elif isinstance(raw_response, dict):
            combined = raw_response.get('text') or raw_response.get('content') or str(raw_response)
        else:
            combined = str(raw_response)

        return combined.strip()
    

    def improve_resume(self, improvement_areas, target_role):
        llm = EuriaiLangChainLLM(api_key=self.api_key, model="gpt-4.1-nano", temperature=0.7, max_tokens=500)
        prompt = (
            f"Suggest improvements in these areas: {', '.join(improvement_areas)} "
            f"for making the resume more suitable for a {target_role} role.\n\n"
            f"Resume content:\n{self.resume_text}"
        )
        raw_response = llm.invoke(prompt)
        return {"suggestions": self._normalize_response(raw_response)}

    def get_improved_resume(self, target_role, highlight_skills):
        llm = EuriaiLangChainLLM(api_key=self.api_key, model="gpt-4.1-nano", temperature=0.5, max_tokens=800)
        prompt = (
            f"Rewrite the resume to improve its alignment for a {target_role} role. "
            f"Highlight these skills: {', '.join(highlight_skills)}.\n\nResume content:\n{self.resume_text}"
        )
        raw_response = llm.invoke(prompt)
        return self._normalize_response(raw_response)

    def cleanup(self):
        for path in self._temp_files:
            if os.path.exists(path):
                os.unlink(path)
        self._temp_files.clear()
