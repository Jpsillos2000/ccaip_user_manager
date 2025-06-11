# data_processor.py
import pandas as pd
import copy
import random

def processar_dataframe(df, template_usuario, platform_users_map, gerar_ramais=False, ramais_existentes=None, team_id_map=None):
    """
    Processa um DataFrame, aplicando todas as regras de negócio para criar ou atualizar usuários.
    """
    if ramais_existentes is None: ramais_existentes = set()
    if team_id_map is None: team_id_map = {}

    novos_usuarios, times_nao_encontrados = [], set()

    colunas_obrigatorias = ['Email', 'Nome', 'Sobrenome', 'Cargo', 'Time']
    if not all(col in df.columns for col in colunas_obrigatorias):
        raise ValueError(f"A planilha deve conter as colunas obrigatórias: {', '.join(colunas_obrigatorias)}")

    nomes_times_validos = {team['name'] for team in template_usuario.get('teams', [])}

    for _, row in df.iterrows():
        if pd.isna(row.get('Email')): continue
        
        novo_usuario = copy.deepcopy(template_usuario)
        email_excel = str(row.get('Email')).strip()
        time_excel = str(row.get('Time')).strip()
        
        # Lógica de Nome e Sobrenome
        first_name, last_name = "", ""
        sobrenome_excel = row.get('Sobrenome')
        if pd.isna(sobrenome_excel) or str(sobrenome_excel).strip() == '':
            nome_completo = str(row.get('Nome', '')).strip()
            partes_nome = nome_completo.split()
            if len(partes_nome) > 1:
                first_name, last_name = partes_nome[0], " ".join(partes_nome[1:])
            else:
                first_name, last_name = nome_completo, ""
        else:
            first_name, last_name = str(row.get('Nome', '')), str(sobrenome_excel)

        # Lógica de geração de ramal por time
        ramal_gerado = ""
        if gerar_ramais and time_excel in team_id_map:
            prefixo = str(team_id_map[time_excel])
            sequencial = 1
            while True:
                num_digitos_seq = 4 - len(prefixo)
                if num_digitos_seq < 1:
                    ramal_gerado = prefixo[:4]
                    break
                formato_seq = f"{{:0{num_digitos_seq}d}}"
                ramal_candidato = f"{prefixo}{formato_seq.format(sequencial)}"
                if ramal_candidato not in ramais_existentes:
                    ramal_gerado = ramal_candidato
                    ramais_existentes.add(ramal_gerado)
                    break
                sequencial += 1
                if sequencial >= 10**num_digitos_seq:
                    print(f"Aviso: Limite de ramais para o time {time_excel} (prefixo {prefixo}) atingido.")
                    ramal_gerado = ""
                    break

        novo_usuario.update({
            'email': email_excel, 'first_name': first_name, 'last_name': last_name,
            'agent_number': None, 'extension_number': ramal_gerado,
            'location': "", 'alias': "", 'new_email': ""
        })

        # Lógica de Roles
        cargo = str(row.get('Cargo')).strip()
        for role in novo_usuario['roles']:
            role['value'] = 1 if (cargo == 'Supervisor' and role['name'] == 'Manager Atendente') or \
                                 (cargo == 'Atendente' and role['name'] == 'Agent') else 0
        
        # Lógica de Times (unificação)
        active_team_names = set()
        if email_excel in platform_users_map:
            novo_usuario['is_new'] = False
            active_team_names.update(team['name'] for team in platform_users_map[email_excel])
        else:
            novo_usuario['is_new'] = True
        
        if pd.notna(time_excel) and time_excel:
            active_team_names.add(time_excel)
        
        for team in novo_usuario['teams']:
            team['value'] = 1 if team['name'] in active_team_names else 0

        if time_excel and time_excel not in nomes_times_validos:
            times_nao_encontrados.add(time_excel)
        
        # Lógica de limite de chats
        limite_chats_valor = row.get('limite de chats')
        if pd.notna(limite_chats_valor) and str(limite_chats_valor).strip() != '':
            novo_usuario['max_chat_limit'] = str(int(float(limite_chats_valor)))
            novo_usuario['max_chat_limit_enabled'] = "1"
        else:
            novo_usuario['max_chat_limit'] = ""
            novo_usuario['max_chat_limit_enabled'] = "0"

        novos_usuarios.append(novo_usuario)
        
    return novos_usuarios, times_nao_encontrados