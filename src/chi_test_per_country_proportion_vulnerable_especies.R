library(jsonlite)
library(dplyr)
library(tidyr)
library(ggplot2)

### Leitura da base de assessments feita com o webscrapping
json_file <- 'C:/Users/caior/Downloads/assessements.json'
json_lines <- readLines(json_file)
dados <- lapply(json_lines, fromJSON)

# Extração da base json
locations_df <- dados %>%
  lapply(function(x) {
    locations <- x$locations
    locations$red_list_category <- x$red_list_category
    locations$year_published <- x$year_published
    locations$scientific_name <- x$taxon$scientific_name
    locations$family_name <- x$taxon$family_name
    locations$class_name <- x$taxon$class_name
    locations$kingdom_name <- x$taxon$kingdom_name
    locations$order_name <- x$taxon$order_name
    locations$phylum_name <- x$taxon$phylum_name
    locations$sis_id <- x$taxon$sis_id
    locations
  }) %>%
  bind_rows()

# Países considerados na análise
paises <- c("Brunei Darussalam","Cambodia","Indonesia","Lao People's Democratic Republic","Malaysia","Myanmar","Philippines","Singapore",'Thailand',"Viet Nam","Brazil","India")

# Retirada dos status de vulnerabilidade não informados
df_filtrado <- filter(locations_df,!(red_list_category %in% c("DD","NE")))

# Filtrar para os países considerados
paises_selecionados <- paises
dados_filtrados <- df_filtrado %>%
  filter(country %in% paises_selecionados)

# Filtrar as espécies com status de vulnerabilidade
status_vulnerabilidade <- c("CR", "EX","Ex",'EW','Ex?')

# Consideraremos somente animais com status de vulnerabilidade maior ou igual à criticamente vulnerável como vulnerável
dados_vulnerabilidade <- dados_filtrados %>%
  mutate(Status.Categorizado = ifelse(red_list_category %in% status_vulnerabilidade, "Vulnerável", "Não Vulnerável"))

# Selecionando o último status antes de 2001
dados_antes_2001 <- dados_vulnerabilidade %>%
  filter(year_published <= 2001) %>%
  group_by(country, scientific_name) %>%
  filter(year_published == max(year_published)) %>%
  mutate(Período = "Antes de 2001")

# Selecionando o primeiro status depois de 2001
dados_depois_2001 <- dados_vulnerabilidade %>%
  filter(year_published > 2001) %>%
  group_by(country, scientific_name) %>%
  filter(year_published == max(year_published)) %>%
  mutate(Período = "Depois de 2001")

# Espécies que possuem status de vulnerabilidade antes e depois de 2001
vec <- unique(dados_antes_2001$scientific_name)[unique(dados_antes_2001$scientific_name) %in% unique(dados_depois_2001$scientific_name)]

# Juntando os dados antes e depois de 2001
dados_final <- bind_rows(dados_antes_2001, dados_depois_2001) %>% filter(scientific_name %in% vec)

# Transformação do problema na tabela de contingência
tabela_contingencia <- dados_final %>%
  group_by(country, Período, Status.Categorizado) %>%
  tally() %>%
  spread(key = Status.Categorizado, value = n, fill = 0)

resultados <- tabela_contingencia %>%
  group_by(country) %>%
  do({
    tabela <- as.matrix(select(., `Vulnerável`, `Não Vulnerável`))  # Seleciona a tabela 2x2
    teste <- chisq.test(tabela)
    data.frame(Valor_P = teste$p.value)
  })

# Exibir as informações sobre o teste
print(resultados)

# Calcular as proporções de espécies em vulnerabilidade por período
dados_proporcoes <- dados_final %>%
  group_by(country, Período, Status.Categorizado) %>%
  tally() %>%  # Contar as espécies em cada status de vulnerabilidade
  group_by(country, Período) %>%
  mutate(Proporcao = n / sum(n))  # Calcular a proporção de cada status dentro de cada país e período

# Plot do gráfico mostrado no ppt
df_limpo <- dados_proporcoes[seq(2, nrow(dados_proporcoes), by = 2), ]
ggplot(df_limpo, aes(x = country, y = Proporcao, fill = Período)) +
  geom_bar(stat = "identity") +
  geom_text(aes(label = scales::percent(Proporcao, accuracy = 0.1)), 
            position = position_stack(vjust = 0.5),  
            color = "black",  
            size = 5,  
            fontface = "bold") +  
  labs(title = "Proporções de espécies vulneráveis por País e Período",
       x = "País",
       y = "Proporção",
       fill = "Período") +
  theme_minimal(base_family = "Arial")  
