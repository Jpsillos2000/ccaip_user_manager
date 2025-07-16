# app/logic/data_processor.py
import pandas as pd
import copy
import random

def gerar_ramal_unico(prefixo, ramais_existentes):
    """Gera um ramal sequencial único para um dado prefixo."""
    sequencial = 1
    while True:
        num_digitos_seq = 4 - len(prefixo)
        if num_digitos_seq < 1: return prefixo[:4]
        
        formato_seq = f"{{:0{num_digitos_seq}d}}"
        ramal_candidato = f"{prefixo}{formato_seq.format(sequencial)}"
        
        if ramal_candidato not in ramais_existentes:
            ramais_existentes.add(ramal_candidato)
            return ramal_candidato
            
        sequencial += 1
        if sequencial >= 10**num_digitos_seq:
            return ""

def processar_dataframe(df, template_usuario, platform_users_map, gerar_ramais=False, ramais_existentes=None, team_id_map=None):
    if ramais_existentes is None: ramais_existentes = set()
    if team_id_map is None: team_id_map = {}

    novos_usuarios, times_nao_encontrados, times_sem_id = [], set(), set()

    # <<< INÍCIO DA NOVA LÓGICA DE COLUNAS FLEXÍVEIS >>>
    # Mapeia os nomes das colunas originais para uma versão padronizada (minúscula)
    column_map = {col.lower().strip(): col for col in df.columns}
    
    # Define as colunas necessárias em minúsculo
    colunas_necessarias = ['email', 'nome', 'sobrenome', 'cargo', 'time', 'matricula']
    
    # Verifica se todas as colunas necessárias existem no mapa
    for col_necessaria in colunas_necessarias:
        if col_necessaria not in column_map:
            raise ValueError(f"A planilha deve conter a coluna obrigatória: '{col_necessaria}' (a capitalização não importa).")

    for _, row in df.iterrows():
        # Função auxiliar para pegar o valor da linha, ignorando a capitalização
        def get_value(col_name):
            original_col_name = column_map.get(col_name.lower())
            if original_col_name and original_col_name in row:
                return row[original_col_name]
            return None

        if pd.isna(get_value('Email')): continue
        
        novo_usuario = copy.deepcopy(template_usuario)
        email_excel = str(get_value('Email')).strip()
        time_excel = str(get_value('Time')).strip()
        
        first_name, last_name = "", ""
        sobrenome_excel = get_value('Sobrenome')
        if pd.isna(sobrenome_excel) or str(sobrenome_excel).strip() == '':
            nome_completo = str(get_value('Nome') or '').strip()
            partes_nome = nome_completo.split()
            if len(partes_nome) > 1:
                first_name, last_name = partes_nome[0], " ".join(partes_nome[1:])
            else:
                first_name, last_name = nome_completo, ""
        else:
            first_name, last_name = str(get_value('Nome') or ''), str(sobrenome_excel)
        
        lookup_key = f"{first_name} {last_name}".strip()
        
        active_team_names = set()
        if lookup_key in platform_users_map:
            novo_usuario['is_new'] = False
            active_team_names.update(team['name'] for team in platform_users_map[lookup_key])
        else:
            novo_usuario['is_new'] = True
        
        if pd.notna(time_excel) and time_excel:
            active_team_names.add(time_excel)

        ramal_gerado = ""
        if gerar_ramais:
            time_de_maior_id_nome, maior_id = None, -1
            for team_name in active_team_names:
                if team_name in team_id_map:
                    current_id = team_id_map[team_name]
                    if current_id > maior_id:
                        maior_id, time_de_maior_id_nome = current_id, team_name
            
            if time_de_maior_id_nome:
                prefixo = str(maior_id)
                ramal_gerado = gerar_ramal_unico(prefixo, ramais_existentes)
            elif time_excel:
                times_sem_id.add(time_excel)
        
        matricula_excel = get_value('matricula')
        agent_number = str(matricula_excel) if pd.notna(matricula_excel) else None

        novo_usuario.update({
            'email': email_excel, 
            'first_name': first_name, 
            'last_name': last_name,
            'agent_number': agent_number,
            'extension_number': ramal_gerado,
            'location': "", 'alias': "", 'new_email': ""
        })

        cargo = str(get_value('Cargo')).strip()
        for role in novo_usuario.get('roles') or []:
            role['value'] = 1 if (cargo == 'Supervisor' and role['name'] == 'Manager Atendente') or (cargo == 'Atendente' and role['name'] == 'Agent') else 0
        
        for team in novo_usuario.get('teams') or []:
            team['value'] = 1 if team['name'] in active_team_names else 0

        if time_excel and time_excel not in {t['name'] for t in template_usuario.get('teams', []) or []}:
            times_nao_encontrados.add(time_excel)
        
        limite_chats_valor = get_value('limite de chats') # Também funciona com case-insensitive
        if pd.notna(limite_chats_valor) and str(limite_chats_valor).strip() != '':
            novo_usuario['max_chat_limit'], novo_usuario['max_chat_limit_enabled'] = str(int(float(limite_chats_valor))), "1"
        else:
            novo_usuario['max_chat_limit'], novo_usuario['max_chat_limit_enabled'] = "", "0"
        
        novos_usuarios.append(novo_usuario)
        
    return novos_usuarios, times_nao_encontrados, times_sem_id