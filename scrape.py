# import os
# import requests
# import json
# from typing import Dict, List

# class GitHubRepoScraper:
#     def __init__(self, github_token=None):
#         self.headers = {
#             'Accept': 'application/vnd.github.v3+json'
#         }
#         if github_token:
#             self.headers['Authorization'] = f'token {github_token}'

#     def scrape_repo_structure(self, repo_url: str) -> Dict[str, List[str]]:
#         # Extract username and repo name
#         parts = repo_url.split('/')
#         username = parts[-2]
#         repo_name = parts[-1]

#         # Base API URL
#         base_url = f'https://api.github.com/repos/{username}/{repo_name}/contents'
        
#         # Scrape repository structure
#         repo_structure = self._get_directory_contents(base_url, '')
#         return repo_structure

#     def _get_directory_contents(self, base_url: str, path: str) -> Dict[str, List[str]]:
#         full_url = f"{base_url}{f'/{path}' if path else ''}"
#         response = requests.get(full_url, headers=self.headers)
        
#         if response.status_code != 200:
#             print(f"Error accessing {full_url}: {response.status_code}")
#             return {}

#         contents = response.json()
#         structure = {
#             'files': [],
#             'directories': {},
#         }

#         for item in contents:
#             if item['type'] == 'file':
#                 structure['files'].append(item['name'])
#             elif item['type'] == 'dir':
#                 dir_path = f"{path}/{item['name']}" if path else item['name']
#                 structure['directories'][item['name']] = self._get_directory_contents(base_url, dir_path)

#         return structure

#     def save_structure_to_file(self, repo_url: str, output_file: str = 'repo_structure.json'):
#         structure = self.scrape_repo_structure(repo_url)
        
#         with open(output_file, 'w') as f:
#             json.dump(structure, f, indent=4)
        
#         print(f"Repository structure saved to {output_file}")

#     def print_structure(self, structure: Dict, indent: int = 0):
#         for key, value in structure.items():
#             print(' ' * indent + str(key) + ':')
#             if isinstance(value, dict):
#                 if 'files' in value:
#                     print(' ' * (indent + 2) + "Files:")
#                     for file in value['files']:
#                         print(' ' * (indent + 4) + file)
                
#                 if 'directories' in value:
#                     print(' ' * (indent + 2) + "Directories:")
#                     for dir_name, dir_contents in value['directories'].items():
#                         print(' ' * (indent + 4) + dir_name + ":")
#                         self.print_structure(dir_contents, indent + 6)

# # Usage Example
# if __name__ == "__main__":
#     repo_url = "https://github.com/Namitha-KS/GT-YOLOv8"
#     scraper = GitHubRepoScraper()
    
#     # Get and print repository structure
#     repo_structure = scraper.scrape_repo_structure(repo_url)
#     scraper.print_structure(repo_structure)
    
#     # Optionally save to JSON
#     scraper.save_structure_to_file(repo_url)


import os
import json
import gradio as gr
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List

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

class ReadmeGenerator:
    def __init__(self, gemini_api_key):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.scraper = GitHubRepoScraper()
    
    def fetch_contributors(self, username, repo_name):
        try:
            contributors_url = f"https://api.github.com/repos/{username}/{repo_name}/contributors"
            response = requests.get(contributors_url)
            if response.status_code == 200:
                return response.json()[:5]  # Limit to top 5 contributors
            return []
        except Exception:
            return []
    
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
        gr.Markdown("# GitHub README Generator")
        repo_link = gr.Textbox(label="GitHub Repository Link")
        generate_btn = gr.Button("Generate README")
        readme_output = gr.Textbox(label="README Content", lines=15)
        preview_btn = gr.Button("Preview Markdown")
        markdown_preview = gr.Markdown()

        generate_btn.click(generator.generate_readme, 
                            inputs=repo_link, 
                            outputs=readme_output)
        
        preview_btn.click(lambda text: text, inputs=readme_output, outputs=markdown_preview)
    
    return demo

if __name__ == "__main__":
    app = create_readme_app()
    app.launch()