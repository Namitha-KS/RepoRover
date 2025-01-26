import os
import json
import gradio as gr
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List

# PDF Generation Imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

class GitHubRepoScraper:
    def __init__(self, github_token=None):
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def scrape_repo_structure(self, repo_url: str) -> Dict[str, List[str]]:
        parts = repo_url.rstrip('/').split('/')
        username = parts[-2]
        repo_name = parts[-1]
        base_url = f'https://api.github.com/repos/{username}/{repo_name}/contents'
        
        repo_structure = self._get_directory_contents(base_url, '')
        return repo_structure, username, repo_name
    
    def _get_directory_contents(self, base_url: str, path: str) -> Dict[str, List[str]]:
        full_url = f"{base_url}{f'/{path}' if path else ''}"
        response = requests.get(full_url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Error accessing {full_url}: {response.status_code}")
            return {}
        
        contents = response.json()
        structure = {
            'files': [],
            'directories': {},
        }
        
        for item in contents:
            if item['type'] == 'file':
                structure['files'].append(item['name'])
            elif item['type'] == 'dir':
                dir_path = f"{path}/{item['name']}" if path else item['name']
                structure['directories'][item['name']] = self._get_directory_contents(base_url, dir_path)
        
        return structure

class PDFGenerator:
    @staticmethod
    def generate_pdf(content: str, filename: str = 'project_report.pdf'):
        """Generate a PDF from text content"""
        os.makedirs('outputs', exist_ok=True)
        filepath = os.path.join('outputs', filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter, 
                                rightMargin=72, leftMargin=72, 
                                topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        paragraphs = content.split('\n\n')
        
        story = []
        for para in paragraphs:
            p = Paragraph(para, styles['Normal'])
            story.append(p)
            story.append(Spacer(1, 12))
        
        doc.build(story)
        return filepath

class ReadmeGenerator:
    def __init__(self, gemini_api_key):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.scraper = GitHubRepoScraper()
        self.pdf_generator = PDFGenerator()
    
    def fetch_contributors(self, username, repo_name):
        try:
            contributors_url = f"https://api.github.com/repos/{username}/{repo_name}/contributors"
            response = requests.get(contributors_url)
            if response.status_code == 200:
                return response.json()[:5]  # Limit to top 5 contributors
            return []
        except Exception:
            return []
    
    def generate_report(self, repo_link):
        """Generate a very detailed project report with detailed insights."""
        try:
            # Scrape repository structure and get username/repo name
            repo_structure, username, repo_name = self.scraper.scrape_repo_structure(repo_link)
            structure_str = json.dumps(repo_structure, indent=2)

            # Fetch repository metadata
            repo_api_url = f"https://api.github.com/repos/{username}/{repo_name}"
            repo_response = requests.get(repo_api_url)
            repo_data = repo_response.json() if repo_response.status_code == 200 else {}

            # Generate comprehensive project report
            prompt = f"""Create a comprehensive project report for the GitHub repository: {repo_link}

Sections to include:
1. 1st page: Cover Page
   - Repository Name
   - Owner/Creator

2. Acknowledgement
   - a 100 word paragraph of acknowledgement

3. Abstract
    - a 100 word paragraph of abstract

4. Introduction
    - a 100 word paragraph of introduction
    - Repository Structure, very briefly just the modules
    - Problem Statement
    - Objective

5. Literature Review
    - pick 15 reference papers from ieee/springer/arxiv
    - a 100 word paragraph of each paper
    
6. Methodology
    - a 500 word paragraph of methodology
    - add methodology diagram
    - add flowchart
    - add UML diagram
    - have a detailed explanation of the concepts used

7. Implementation
    - a 500 word paragraph of implementation
    - system requirements
    - installation guide
    - software requirements
    - hardware requirements
    - add code snippets
    - add screenshots of the code
    - add screenshots of the output
    - add screenshots of the UI
    
8. Results
    - a 500 word paragraph of results
    
9. Discussion
    - a 100 word paragraph of discussion

10. Conclusion
    - a 100 word paragraph of conclusion
    
11. Future Scope

12. References
    - add all 15 references used

Provide insights, recommendations, and a professional assessment."""

            response = self.model.generate_content(prompt)
            report_text = response.text
            
            # Generate PDF
            pdf_path = self.pdf_generator.generate_pdf(report_text, f'{repo_name}_project_report.pdf')
            
            # Return both text and PDF path
            return f"{report_text}\n\n--- PDF Generated: {pdf_path} ---"

        except Exception as e:
            return f"Error generating report: {str(e)}"

    def generate_assets(self, repo_link):
        """Generate project visualization and marketing assets."""
        try:
            # Scrape repository structure and get username/repo name
            repo_structure, username, repo_name = self.scraper.scrape_repo_structure(repo_link)

            # Fetch repository metadata
            repo_api_url = f"https://api.github.com/repos/{username}/{repo_name}"
            repo_response = requests.get(repo_api_url)
            repo_data = repo_response.json() if repo_response.status_code == 200 else {}

            # Generate assets description prompt
            prompt = f"""Generate a set of project assets for the GitHub repository: {repo_link}

Assets to create:
1. Project Logo Concept (SVG description)
2. ReadMe Banner Image Concept
3. Social Media Share Graphics
   - Twitter/X Card
   - LinkedIn Post Graphic
4. Project Badges
   - Technology Badges
   - Status Badges

Provide detailed descriptions and SVG/design concepts for each asset."""

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"Error generating assets: {str(e)}"

    def generate_readme(self, repo_link):
        if not repo_link:
            return "Please enter a GitHub repository link"

        try:
            # Scrape repository structure and get username/repo name
            repo_structure, username, repo_name = self.scraper.scrape_repo_structure(repo_link)
            structure_str = json.dumps(repo_structure, indent=2)

            # Fetch repository metadata
            repo_api_url = f"https://api.github.com/repos/{username}/{repo_name}"
            repo_response = requests.get(repo_api_url)
            repo_data = repo_response.json() if repo_response.status_code == 200 else {}

            # Fetch contributors
            contributors = self.fetch_contributors(username, repo_name)

            # Generate README with comprehensive details
            prompt = f"""Generate a comprehensive README.md for the GitHub repository: {repo_link}

Repository Structure:
{structure_str}

Repository Metadata:
- Stars: {repo_data.get('stargazers_count', 'N/A')}
- Forks: {repo_data.get('forks_count', 'N/A')}
- Primary Language: {repo_data.get('language', 'N/A')}

Create a README with these specific sections:
1. Project Title and Brief Description
2. Table of Contents
3. Detailed Project Explanation
4. Installation Instructions
5. Usage Guide
6. Dependencies and Requirements
7. Key Features (in table format)
8. Contribution Guidelines with Contributor Details (if available)
9. MIT License Text

Ensure the README is professional, informative, and well-structured."""

            response = self.model.generate_content(prompt)
            readme_text = response.text

            # Remove any already generated license section
            license_header = "## License"
            if license_header in readme_text:
                readme_text = readme_text.split(license_header)[0].strip()  # Remove existing license

            # Append Contributors section only if contributors exist
            if contributors:
                contributors_section = "\n## Contributors\n\n"
                for contrib in contributors:
                    contributors_section += f"- [{contrib['login']}]({contrib['html_url']}) - {contrib['contributions']} contributions\n"
                readme_text += contributors_section  # Add to README

            # Append MIT License
            mit_license = f"""\n## License

MIT License

Copyright (c) {repo_data.get('created_at', '')[:4]} {username}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

            readme_text += mit_license  # Append cleaned license

            return readme_text

        except Exception as e:
            return f"Error generating README: {str(e)}"

# Gradio Interface
def create_readme_app():
    load_dotenv()
    API_KEY = os.getenv("API-KEY")
    
    generator = ReadmeGenerator(API_KEY)
    
    with gr.Blocks() as demo:
        gr.Markdown("# RepoRover : AI generated documentations for projects")
        repo_link = gr.Textbox(label="GitHub Repository Link")
        
        with gr.Row():
            generate_btn = gr.Button("Generate README")
            report_btn = gr.Button("Generate Report")
            assets_btn = gr.Button("Generate Assets")
        
        output_tabs = gr.Tabs()
        with output_tabs:
            with gr.TabItem("README"):
                readme_output = gr.Textbox(label="README Content", lines=15)
                preview_btn = gr.Button("Preview Markdown")
                markdown_preview = gr.Markdown()
            
            with gr.TabItem("Report"):
                report_output = gr.Textbox(label="Project Report", lines=15)
                pdf_output = gr.File(label="Download PDF Report")
            
            with gr.TabItem("Assets"):
                assets_output = gr.Textbox(label="Project Assets", lines=15)

        generate_btn.click(generator.generate_readme, 
                            inputs=repo_link, 
                            outputs=readme_output)
        
        report_btn.click(generator.generate_report, 
                          inputs=repo_link, 
                          outputs=[report_output, pdf_output])
        
        assets_btn.click(generator.generate_assets, 
                          inputs=repo_link, 
                          outputs=assets_output)
        
        preview_btn.click(lambda text: text, inputs=readme_output, outputs=markdown_preview)
    
    return demo

if __name__ == "__main__":
    app = create_readme_app()
    app.launch()