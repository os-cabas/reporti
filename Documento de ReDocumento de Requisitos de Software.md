# **Backlog Mínimo Viável (MVP)**

# Se for um projeto acadêmico ou primeira versão, eu priorizaria:

1. # Login Google / Magic Link

2. # Cadastro de Entidades

3. # Cadastro de Técnicos

4. # Cadastro de Salas

5. # Cadastro de Equipamentos

6. # Abertura de Chamados

7. # Atendimento de Chamados

8. # Registro de Manutenção

9. # Histórico de Equipamentos

10. # Dashboard Básico

    

# **Requisitos de Software**

## **1\. Visão Geral**

### **1.1 Objetivo**

Desenvolver uma plataforma web para gerenciamento de ativos tecnológicos e controle de chamados técnicos em instituições de ensino, empresas e organizações.

O sistema permitirá que usuários reportem problemas em equipamentos por meio de um código identificador único, enquanto técnicos e administradores poderão gerenciar dispositivos, manutenções, salas, laboratórios e chamados.

---

# **2\. Perfis de Usuário**

## **2.1 Usuário Comum**

Usuário responsável por reportar problemas em equipamentos.

## **2.2 Técnico**

Usuário responsável pela manutenção dos equipamentos e atendimento dos chamados.

## **2.3 Administrador da Entidade**

Usuário responsável pela administração de uma organização específica.

## **2.4 Administrador Geral**

Usuário responsável pela administração global da plataforma.

---

# **3\. Requisitos Funcionais**

## **RF001 – Autenticação via Google**

Descrição:  
Permitir login utilizando conta Google institucional.

Fluxo:

1. Usuário seleciona "Entrar com Google".  
2. Sistema redireciona para autenticação Google.  
3. Google valida credenciais.  
4. Sistema cria ou recupera usuário.  
5. Usuário é direcionado para a página inicial.

Critérios de Aceitação:

* Apenas domínios cadastrados na autorizados podem acessar.  
* Login deve ser concluído sem cadastro manual.

---

## **RF002 – Login por Link Mágico**

Descrição:  
Permitir autenticação através de link enviado ao e-mail.

Fluxo:

1. Usuário informa e-mail.  
2. Sistema envia link temporário.  
3. Usuário acessa o link.  
4. Sistema autentica automaticamente.

Critérios:

* Link deve expirar em até 15 minutos.  
* Link pode ser utilizado apenas uma vez.

---

## **RF003 – Cadastro de Entidade**

Descrição:  
Permitir que o administrador geral cadastre novas organizações.

Campos:

* Nome  
* Tipo  
* E-mail responsável  
* Descrição  
* Status

Critérios:

* Não permitir entidades duplicadas.  
* Registrar data de criação.

---

## **RF004 – Cadastro de Usuários**

Descrição:  
Permitir cadastro de usuários vinculados a uma entidade.

Campos:

* Nome  
* E-mail  
* Cargo  
* Perfil

Critérios:

* E-mail único no sistema.  
* Usuário inicia como ativo.

---

## **RF005 – Gerenciamento de Técnicos**

Descrição:  
Permitir ao administrador da entidade criar técnicos.

Permissões:

* Criar  
* Editar  
* Desativar  
* Redefinir senha

Critérios:

* Apenas administradores da entidade possuem acesso.

---

## **RF006 – Gerenciamento de Permissões**

Descrição:  
Permitir atribuir permissões específicas aos técnicos.

Exemplos:

* Gerenciar dispositivos  
* Gerenciar laboratórios  
* Gerenciar chamados  
* Gerenciar usuários

Critérios:

* Sistema deve validar permissões em todas as ações.

---

## **RF007 – Cadastro de Salas**

Descrição:  
Permitir criação de salas físicas.

Campos:

* Nome  
* Bloco  
* Andar  
* Observação

Critérios:

* Nome não pode ser duplicado dentro da mesma entidade..

---

## **RF009 – Cadastro de Dispositivos**

Descrição:  
Permitir cadastro de equipamentos.

Campos:

* Código identificador (QR Code)  
* Patrimônio  
* Tipo  
* Marca  
* Modelo  
* Número de série  
* Situação

Critérios:

* Código identificador único.  
* Histórico deve ser preservado.

---

## **RF010 – Associação de Equipamentos**

Descrição:  
Permitir vincular dispositivos a salas e laboratórios.

Critérios:

* Cada dispositivo deve possuir localização atual.

---

## **RF011 – Alteração de Status de Equipamento**

Descrição:  
Permitir atualização do estado operacional.

Status possíveis:

* Operacional  
* Em manutenção  
* Reservado  
* Inativo  
* Descartado

Critérios:

* Todas alterações devem ser registradas em histórico.

---

## **RF012 – Atendimento de Chamados**

Descrição:  
Permitir que técnicos assumam chamados.

Ações:

* Assumir  
* Atualizar  
* Resolver  
* Encerrar

Critérios:

* Todas as ações devem gerar histórico.

---

## **RF013 – Registro de Manutenção**

Descrição:  
Permitir registrar manutenções.

Campos:

* Tipo  
* Descrição  
* Data início  
* Data fim  
* Técnico responsável

Critérios:

* A manutenção deve ficar vinculada ao equipamento.

---

## **RF014 – Histórico de Equipamentos**

Descrição:  
Permitir consulta de todo histórico.

Informações:

* Mudanças de status  
* Manutenções  
* Chamados  
* Movimentações

---

## **RF015 – Dashboard**

Descrição:  
Exibir indicadores operacionais.

Indicadores:

* Equipamentos ativos  
* Equipamentos em manutenção  
* Chamados abertos  
* Chamados concluídos  
* Técnicos ativos

---

# **4\. Regras de Negócio**

## **RN001**

Cada equipamento deve possuir um código identificador único.

## **RN002**

Um chamado deve estar associado a apenas um equipamento.

## **RN003**

Um técnico pode atender múltiplos chamados.

## **RN004**

Um chamado encerrado não pode ser editado.

## **RN005**

Administradores de entidade não podem acessar dados de outras entidades.

## **RN006**

Apenas administradores gerais podem criar novas entidades.

## **RN007**

Toda alteração de status de equipamento deve gerar histórico.

## **RN008**

Toda manutenção deve possuir técnico responsável.

# **Usuários e acessos:**

# **Usuário Comum**

Responsável apenas por reportar e acompanhar problemas.

### **Pode:**

✅ Fazer login

✅ Visualizar seus próprios chamados

✅ Abrir chamados

✅ Anexar imagens e documentos

✅ Adicionar comentários aos seus chamados

✅ Consultar status dos chamados

✅ Receber notificações

### **Não pode:**

❌ Visualizar chamados de outros usuários

❌ Alterar equipamentos

❌ Criar salas

❌ Criar laboratórios

❌ Registrar manutenção

❌ Gerenciar usuários

---

# **Técnico**

Responsável pela operação e manutenção dos ativos.

### **Pode:**

✅ Fazer login

✅ Visualizar chamados da entidade

✅ Assumir chamados

✅ Alterar status dos chamados

✅ Registrar atendimento

✅ Registrar manutenção

✅ Consultar histórico de equipamentos

✅ Cadastrar equipamentos

✅ Editar equipamentos

✅ Alterar situação dos equipamentos

✅ Criar salas

✅ Criar laboratórios

✅ Associar equipamentos a salas

✅ Mover equipamentos entre salas

### **Dependendo da permissão concedida:**

✅ Excluir equipamentos

✅ Criar outros técnicos

✅ Aprovar manutenções

### **Não pode:**

❌ Criar entidades

❌ Acessar dados de outras entidades

❌ Alterar configurações globais

---

# **Administrador da Entidade**

Responsável pela gestão da organização.

### **Pode:**

✅ Tudo que o técnico faz

✅ Cadastrar técnicos

✅ Editar técnicos

✅ Desativar técnicos

✅ Redefinir senhas

✅ Criar cargos

✅ Criar grupos de permissões

✅ Gerenciar usuários da entidade

✅ Gerenciar salas

✅ Gerenciar laboratórios

✅ Gerenciar equipamentos

✅ Visualizar relatórios

✅ Visualizar todos os chamados da entidade

✅ Definir responsáveis por laboratórios

✅ Configurar informações da entidade

### **Não pode:**

❌ Criar novas entidades

❌ Excluir entidades

❌ Gerenciar entidades de terceiros

❌ Acessar informações globais da plataforma

---

# **Administrador Geral**

Responsável pela plataforma inteira.

### **Pode:**

✅ Criar entidades

✅ Editar entidades

✅ Desativar entidades

✅ Criar administradores de entidade

✅ Gerenciar qualquer usuário

✅ Visualizar relatórios globais

✅ Acessar todas as entidades

✅ Configurar sistema

✅ Gerenciar permissões globais

✅ Auditar logs

✅ Gerenciar integrações

✅ Configurar autenticação Google

### **Não pode:**

❌ Apenas ações restritas pelo próprio sistema (ex.: exclusão permanente de logs de auditoria, se vocês decidirem proteger isso).

