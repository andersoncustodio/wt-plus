## wt+

wt+ is a development environment for Ubuntu Linux (soon in other linux distributions and macOS). No Vagrant, no Docker and **automatic** `/etc/hosts` management.



### Pre-alpha project

Este projeto ainda precisa de muitas melhorias, alguns ajustes manuais podem ser necessários.

### Instalação

Instalando e atualizando usando [pip](https://pip.pypa.io/en/stable/getting-started/):

```shell
pip install -U wt-plus
```

### Autocomplet e path

#### bash

Adicione no arquivo `~/.bashrc`

```shell
export PATH=$PATH:$HOME/.local/bin
eval "$(_WT_COMPLETE=bash_source wt)"
```
Carregue a nova configuração no terminal atual com `source ~/.bashrc`

#### zsh

Adicione no arquivo `~/.zshrc`

```shell
export PATH=$PATH:$HOME/.local/bin
eval "$(_WT_COMPLETE=zsh_source wt)"
```

Carregue a nova configuração no terminal atual com `source ~/.zshrc`

### Instalando e configurando ambiente

Isso pode demorar um pouco, várias versões do `PHP` serão instaladas com outros serviços `redis`, `mailhog` e `RabbitMQ`

```shell
wt services configure
```

Se tudo ocorreu bem o `mailhog` já está acessível [mailhog.test](https://mailhog.test/)

```shell
wt links
```

### Rodando seu primeiro PHP no wt+

#### Sites

Embora o funcionamento interno do wt+ seja diferente do Vallet+ os comandos são iguais. Vamos para alguns exemplos práticos.

```shell
mkdir paginadeteste
cd paginadeteste
printf "<?php\nphpinfo();\n" > index.php
wt link
```

Acesse [paginadeteste.test](https://paginadeteste.test/)

Caso o diretório do projeto tenha um nome complicado ou repetido de outro projeto você pode especificar outro nome.

```shell
wt link outronomeparaosite
```

Você pode remover esse link adicional

```shell
wt unlink outronomeparaosite
```

No wt+ cada site tem sua versão do PHP.


```shell
wt use 5.6
```

```shell
wt use 7.4
```

```shell
wt use 8.0
```

Se você não especificar versão do PHP o terminal será setado com a versão utilizada no projeto.

```shell
wt use
```

Também é possível alterar a versão do site e do terminal em simultâneo.

```shell
wt use 8.0 --update-cli
```

#### Aliases e subdomínios

Você também pode adicionar vários alias com o nome que desejar e sem se preocupar com a extensão do domínio, pois o wt+ faz a configuração em seu arquivo `/etc/hosts`

```shell
wt alias paginateste1.test
wt alias paginateste2.test
wt alias alguma.paginateste3.dev
```

Gere um novo certificado que contemple os aliases adicionados.

```shell
wt secure
```

Também é possível remover um alias facilmente.

```shell
wt unalias paginateste2.test
```

### Instalando banco de dados

Caso você não tenha instalado o MySQL

```shell
sudo apt install mariadb-server
```

Alterando a senha do root

```shell
sudo mysql
```

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';
FLUSH PRIVILEGES;
```

### Configurando acesso ao banco de dados

Informe o usuário e senha utilizado para acessar o banco de dados pelo terminal local em `~/.my.cnf`

```ini
[client]
user = root
password = root
```

### Comandos para manipular o banco de dados

Listar

```shell
wt db ls
```

Caso o diretório atual esteja dentro do `path` de um site o banco será criado com o nome do mesmo


#### create

```shell
wt db create
```

Caso o diretório atual esteja fora de um site ou você queria definir um nome diferente para o banco é possível definir com outro parâmetro

```shell
wt db create outronome
```

#### import

```shell
wt db import backup.sql
```

```shell
wt db import backup.sql outronome
```

