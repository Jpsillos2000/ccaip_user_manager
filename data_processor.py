# data_processor.py
import pandas as pd
import copy

def processar_dataframe(df, template_usuario):
    """
    Processa um DataFrame do pandas e o converte em uma lista de dicionários de usuários.
    """
    novos_usuarios, times_nao_encontrados = [], set()

    colunas_obrigatorias = ['Email', 'Nome', 'Sobrenome', 'Cargo', 'Time']
    if not all(col in df.columns for col in colunas_obrigatorias):
        raise ValueError(f"A planilha deve conter as colunas obrigatórias: {', '.join(colunas_obrigatorias)}")

    nomes_times_validos = {team['name'] for team in template_usuario.get('teams', [])}
    for _, row in df.iterrows():
        if pd.isna(row.get('Email')): continue
        
        novo_usuario = copy.deepcopy(template_usuario)
        
        novo_usuario.update({
            'email': str(row.get('Email')), 'first_name': str(row.get('Nome')),
            'last_name': str(row.get('Sobrenome')), 'agent_number': None,
            'location': "", 'alias': "", 'new_email': ""
        })

        cargo, time = str(row.get('Cargo')).strip(), str(row.get('Time')).strip()
        for role in novo_usuario['roles']:
            role['value'] = 1 if (cargo == 'Supervisor' and role['name'] == 'Manager Atendente') or \
                                 (cargo == 'Atendente' and role['name'] == 'Agent') else 0
        for team in novo_usuario['teams']:
            team['value'] = 1 if team['name'] == time else 0
        if time not in nomes_times_validos and pd.notna(time):
            times_nao_encontrados.add(time)
        
        limite_chats_valor = row.get('limite de chats')
        if pd.notna(limite_chats_valor) and str(limite_chats_valor).strip() != '':
            novo_usuario['max_chat_limit'] = str(int(float(limite_chats_valor)))
            novo_usuario['max_chat_limit_enabled'] = "1"
        else:
            novo_usuario['max_chat_limit'] = ""
            novo_usuario['max_chat_limit_enabled'] = "0"

        novos_usuarios.append(novo_usuario)
        
    return novos_usuarios, times_nao_encontrados