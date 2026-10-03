"""Conteúdo autoral inicial: fundamentos revisáveis, sem execução de comandos."""
COURSE = {
 'id':'network-fundamentals', 'title':'Fundamentos de redes', 'edition':1,
 'status':'Conteúdo introdutório autoral; aprofunde e confira com o tutor.',
 'modules':[
  {'id':'addressing','title':'1 · Endereços e caminhos','lessons':[
   {'id':'ip','title':'IP, sub-rede e gateway',
    'body':'Um endereço IP identifica uma interface dentro de uma rede IP. A máscara ou o prefixo define quais bits identificam a rede. Em 192.168.56.10/24, os primeiros 24 bits identificam a rede; 192.168.56.20 pertence à mesma sub-rede.\n\nPara enviar um pacote a outro destino, o sistema consulta sua tabela de rotas. Quando a rota usa um gateway, a máquina entrega o quadro ao próximo salto, mantendo no pacote IP o destino final. O gateway não é sinônimo de servidor DNS.\n\nExercício: compare 192.168.56.10/24, 192.168.56.20/24 e 192.168.57.20/24. Os dois primeiros compartilham a sub-rede. O terceiro normalmente exige uma rota por outro próximo salto. A configuração real da tabela de rotas determina o caminho.\n\nErro comum: deduzir conectividade só pelo endereço. Firewall, interface inativa e rotas também importam.',
    'quiz':{'question':'Qual é a função principal de um gateway padrão?','choices':['Resolver nomes DNS','Ser o próximo salto quando nenhuma rota mais específica se aplica','Criptografar todo tráfego'],'answer':1,'explanation':'O sistema escolhe a rota mais específica. A rota padrão é usada quando não existe outra rota aplicável mais específica.'}},
   {'id':'dns','title':'DNS: nomes e registros',
    'body':'DNS associa nomes a informações por meio de registros. A aponta para IPv4; AAAA para IPv6. Um resolvedor pode responder a partir do cache ou consultar servidores. TTL indica por quanto tempo uma resposta pode permanecer no cache, sujeito às políticas do resolvedor.\n\nDNS não torna um serviço automaticamente acessível: um nome pode resolver corretamente enquanto a conexão falha. Separe falha de resolução, falha de rota e recusa de conexão.\n\nExercício: desenhe o percurso nome → resolvedor → resposta → conexão ao endereço. O resolvedor e o servidor da aplicação podem ser máquinas diferentes.\n\nDefesa: registrar mudanças de configuração do resolvedor e conferir a procedência de respostas ajuda a investigar desvios. Um registro DNS não comprova a identidade de um serviço; a validação de certificados TLS tem outro papel.',
    'quiz':{'question':'Qual registro contém um endereço IPv6?','choices':['A','MX','AAAA'],'answer':2,'explanation':'AAAA contém IPv6. A contém IPv4; MX indica servidores de correio.'}}
  ]},
  {'id':'transport','title':'2 · Transporte e aplicações','lessons':[
   {'id':'tcp','title':'TCP, UDP e criptografia',
    'body':'TCP fornece um fluxo de bytes ordenado com mecanismos de confirmação e retransmissão. A aplicação ainda precisa definir como separar suas mensagens dentro desse fluxo. TCP não garante que a aplicação remota processou uma operação apenas porque bytes foram confirmados.\n\nUDP envia datagramas sem garantir entrega, ordem ou ausência de duplicatas. A aplicação pode implementar suas próprias garantias. Menos mecanismos no transporte não significa que UDP será sempre mais rápido em qualquer cenário.\n\nNenhum desses protocolos, por si só, criptografa o conteúdo da aplicação. TLS é uma camada adicional; QUIC combina transporte sobre UDP com proteção criptográfica.\n\nExercício: descreva o que acontece se um segmento TCP se perde. Compare com um datagrama UDP perdido. Explique por que confiabilidade e confidencialidade são propriedades diferentes.\n\nDefesa: observe padrões de conexão e retransmissão antes de concluir que existe ataque. Congestionamento e falhas de enlace também causam anomalias.',
    'quiz':{'question':'TCP, por si só, criptografa o conteúdo?','choices':['Não; confiabilidade e criptografia são propriedades distintas','Sim, durante o handshake','Sim, quando a porta é 443'],'answer':0,'explanation':'TCP não fornece criptografia do conteúdo. A porta 443 é uma convenção de serviço; o uso efetivo de TLS é que fornece proteção criptográfica.'}}
  ]}
 ]
}

LABS = [
 {'id':'loopback','title':'Conectividade com a própria máquina','level':'Iniciante · Windows',
  'objective':'Relacionar loopback, endereçamento e resposta ICMP sem acessar terceiros.',
  'requirements':['Windows com PowerShell ou Prompt de Comando.','Não exige administrador nem instalação.'],
  'isolation':'O endereço 127.0.0.1 representa esta própria máquina. Este roteiro usa somente loopback.',
  'steps':[
   {'title':'Observar a resposta local','command':'ping -n 4 127.0.0.1','explanation':'ping envia solicitações ICMP Echo. -n 4 limita o envio a quatro solicitações no Windows. 127.0.0.1 seleciona loopback; os pacotes não atravessam a placa de rede física.','expected':'Quatro tentativas e um resumo. A formatação e o tempo variam. Sucesso confirma a resposta local, não acesso à internet.'},
   {'title':'Examinar a configuração','command':'ipconfig','explanation':'Mostra endereços e parâmetros dos adaptadores locais. Não altera a configuração. Compare o endereço de uma interface com loopback.','expected':'Adaptadores, endereços e, quando configurado, gateway. Adaptadores virtuais podem aparecer.'}],
  'errors':['Falha no ping pode refletir filtragem local ou configuração; não prova que a internet caiu.','ipconfig pode exibir várias interfaces; não confunda adaptadores virtuais com o adaptador ativo.'],
  'defense':'Uma resposta ICMP não prova que um serviço está seguro. Na investigação, associe conectividade a rotas, firewall e logs pertinentes.',
  'cleanup':'Nenhuma configuração ou arquivo é modificado. Não há limpeza necessária.',
  'reflection':'Por que ping em loopback pode funcionar mesmo sem cabo e sem Wi-Fi?'},
 {'id':'file-integrity','title':'Integridade de um arquivo com SHA-256','level':'Iniciante · PowerShell',
  'objective':'Comparar hashes e distinguir integridade de autenticidade.',
  'requirements':['PowerShell no Windows.','Um arquivo de teste criado por você, sem informação sensível.'],
  'isolation':'Trabalho somente sobre arquivo local. Nenhum upload ou conexão de rede é necessário.',
  'steps':[
   {'title':'Escolher o arquivo','command':None,'explanation':'Crie um pequeno arquivo de texto numa pasta de estudos e copie seu caminho. Nos próximos comandos, substitua o caminho de exemplo pelo caminho real.','expected':'Um arquivo descartável de sua autoria.'},
   {'title':'Calcular o resumo','command':"Get-FileHash -LiteralPath 'C:\\Estudos\\amostra.txt' -Algorithm SHA256",'explanation':'Get-FileHash lê o arquivo. -LiteralPath trata o caminho literalmente, sem curingas. -Algorithm SHA256 escolhe o algoritmo. O comando não modifica o arquivo.','expected':'Um hash hexadecimal de 64 caracteres, algoritmo e caminho. Guarde o resultado.'},
   {'title':'Comparar após alteração','command':None,'explanation':'Edite uma palavra no arquivo, salve e repita o cálculo. Compare os valores.','expected':'O hash deve mudar. Um hash conhecido só comprova autenticidade se sua referência vier de uma fonte confiável.'}],
  'errors':['Caminho não encontrado: confira o nome e a extensão do arquivo.','Acesso negado: escolha um arquivo próprio legível; este exercício não requer elevação.'],
  'defense':'Hashes ajudam a detectar alterações, mas um invasor que controla o arquivo e a referência pode substituir ambos. Assinaturas digitais e distribuição confiável complementam a verificação.',
  'cleanup':'Se desejar, remova somente o arquivo de teste criado por você.',
  'reflection':'Por que baixar um arquivo e seu hash do mesmo local comprometido não garante autenticidade?'}
]
