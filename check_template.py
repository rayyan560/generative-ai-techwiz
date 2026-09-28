import os, sys

filepath = r'c:\Users\rayyan\Desktop\generative-ai-techwiz-main\templates\documentation.html'

content = open(r'c:\Users\rayyan\Desktop\generative-ai-techwiz-main\templates\knowledge_base.html', 'r', encoding='utf-8').read()[:200]
print("Example template first 200 chars:")
print(content)
