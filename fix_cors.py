# Ler o arquivo main.py
with open('app/main.py', 'r') as f:
    lines = f.readlines()

# Procurar onde adicionar CORS
new_lines = []
cors_added = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Adicionar após as importações do FastAPI
    if 'from fastapi import FastAPI' in line and not cors_added:
        new_lines.append('from fastapi.middleware.cors import CORSMiddleware\n')
        cors_added = True
    
    # Adicionar configuração CORS após app = FastAPI()
    if 'app = FastAPI' in line:
        # Encontrar o final da definição do FastAPI
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith(')'):
            j += 1
        
        # Adicionar CORS depois
        new_lines.append('\n# Configurar CORS\n')
        new_lines.append('app.add_middleware(\n')
        new_lines.append('    CORSMiddleware,\n')
        new_lines.append('    allow_origins=["*"],\n')
        new_lines.append('    allow_credentials=True,\n')
        new_lines.append('    allow_methods=["*"],\n')
        new_lines.append('    allow_headers=["*"],\n')
        new_lines.append(')\n')

# Salvar
with open('app/main.py', 'w') as f:
    f.writelines(new_lines)

print("✅ CORS adicionado!")
