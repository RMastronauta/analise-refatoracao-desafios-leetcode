import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

from repository.repository import Repository

class GeradorGrafico:
    def __init__(self):
        self.repository = Repository()
        
        sns.set_theme(style="whitegrid", context="paper")
        plt.rcParams.update({
            'figure.figsize': [12, 6],
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'savefig.dpi': 300, 
            'figure.autolayout': True 
        })
        
        # Pasta de saída para as imagens
        self.output_dir = "resultados_tcc_graficos_finais"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def salvar_figura(self, nome_arquivo):
        """Auxiliar para salvar e limpar a memória do Matplotlib"""
        caminho = os.path.join(self.output_dir, nome_arquivo)
        plt.savefig(caminho, bbox_inches='tight')
        print(f"Gráfico final salvo em: {caminho}")
        plt.close()

    def gerar_todos_os_graficos(self):
        print("Buscando dados atualizados no banco de dados...")
        resultados = self.repository.getAllResultados()
        df = pd.DataFrame(resultados)
        
        if df.empty:
            print("Erro: O DataFrame está vazio. Verifique a sintaxe SQL e a conexão.")
            return

        print(f"Processando {len(df)} registros para visualização final...")

        self.plot_boxplot_complexidade_zoom(df)
        self.plot_barras_llm_divida_final(df)
        self.plot_facet_code_smells_final(df)
        self.plot_scatter_loc_complexidade_densidade(df)
        self.plot_scatter_loc_complexidade_zoom(df)
        self.plot_boxplot_loc_zoom(df)
        
        print(f"\n✅ Processo concluído! Gráficos salvos na pasta '{self.output_dir}'.")

    def plot_boxplot_complexidade_zoom(self, df):
        """Gráfico 1: Impacto da refatoração na Complexidade com Zoom nos dados principais"""
        plt.figure(figsize=(10, 6))
        
        sns.boxplot(
            data=df, 
            x='tipo', 
            y='complexidade_ciclomatica', 
            hue='linguagem', 
            palette='Set2',
            showmeans=True,
            meanprops={"marker":"D", "markerfacecolor":"white", "markeredgecolor":"black", "markersize":"6"}
        )
        
        plt.title('Distribuição da Complexidade Ciclomática por Estratégia')
        plt.ylabel('Complexidade (Sonar)')
        plt.xlabel('Tipo de Código')
        
        plt.ylim(-2, 60) 
        
        self.salvar_figura('01_boxplot_complexidade_zoom.png')

    def plot_barras_llm_divida_final(self, df):
        """Gráfico 2: Qual LLM gera código com menor dívida técnica média"""
        plt.figure(figsize=(12, 6))
        
        df_grouped = df.groupby(['modelo', 'tipo'])['divida_tecnica'].mean().reset_index()
        
        sns.barplot(data=df_grouped, x='modelo', y='divida_tecnica', hue='tipo', palette='mako')
        
        plt.title('Média de Dívida Técnica por Modelo e Prompt')
        plt.ylabel('Dívida Técnica (minutos)')
        plt.xlabel('LLM')
        
        plt.legend(title='Estratégia', bbox_to_anchor=(1.01, 1), loc='upper left')
        self.salvar_figura('02_media_divida_tecnica_llm.png')

    def plot_facet_code_smells_final(self, df):
        """Gráfico 3: Comparação detalhada de Code Smells por Linguagem e Modelo"""
        g = sns.FacetGrid(df, col="linguagem", height=5, aspect=1.2, sharey=True)
        
        g.map_dataframe(sns.barplot, x="modelo", y="code_smells", hue="tipo", palette='rocket', errorbar=None)
        
        g.set_axis_labels("Modelos", "Média de Code Smells")
        g.add_legend(title="Estratégia")
        
        plt.subplots_adjust(top=0.80) 
        g.fig.suptitle('Code Smells Médios: Comparativo entre Java e Python', fontsize=16)
        
        caminho = os.path.join(self.output_dir, '03_facet_code_smells.png')
        g.savefig(caminho, dpi=300)
        plt.close()

    def plot_scatter_loc_complexidade_densidade(self, df):
        """Gráfico 4: Correlação entre tamanho do código e complexidade com ajuste de densidade"""
        plt.figure(figsize=(10, 7))
        
        sns.scatterplot(
            data=df, 
            x='loc', 
            y='complexidade_ciclomatica', 
            hue='tipo', 
            style='linguagem', 
            alpha=0.3,
            s=20 
        )
        
        plt.title('Correlação: Tamanho do Código (LOC) vs Complexidade')
        plt.xlabel('Linhas de Código (ncloc)')
        plt.ylabel('Complexidade Ciclomática')
        plt.grid(True, linestyle=':', alpha=0.6)
        
        
        self.salvar_figura('04_dispersao_loc_complexidade_densidade.png')

    def plot_scatter_loc_complexidade_zoom(self, df):
        """Gráfico 4 (Opção A): Dispersão com Zoom para remover outlier extremo"""
        plt.figure(figsize=(10, 7))
        sns.scatterplot(
            data=df, 
            x='loc', 
            y='complexidade_ciclomatica', 
            hue='tipo', 
            style='linguagem', 
            alpha=0.3,
            s=15
        )
        
        plt.title('Correlação: LOC vs Complexidade (Foco na Maioria dos Dados)')
        plt.xlabel('Linhas de Código (ncloc)')
        plt.ylabel('Complexidade Ciclomática')
        plt.grid(True, linestyle=':', alpha=0.6)
        
        plt.xlim(-5, 160)
        plt.ylim(-2, 80) 
        
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
        
        self.salvar_figura('04_dispersao_loc_complexidade_zoom.png')

    def plot_boxplot_loc_zoom(self, df):
        """Gráfico 5: Verificação do volume de código com Zoom e Médias"""
        plt.figure(figsize=(10, 6))
        
        sns.boxplot(
            data=df, 
            x='linguagem', 
            y='loc', 
            hue='tipo', 
            palette='pastel',
            showmeans=True,
            meanprops={"marker":"D", "markerfacecolor":"white", "markeredgecolor":"black", "markersize":"6"}
        )
        
        plt.title('Variação de Linhas de Código (LOC) por Estratégia')
        plt.ylabel('LOC (ncloc)')
        plt.xlabel('Linguagem')
        
        plt.ylim(-5, 150)
        
        self.salvar_figura('05_boxplot_loc_zoom.png')

# Execução do script
if __name__ == "__main__":
    gerador = GeradorGrafico()
    gerador.gerar_todos_os_graficos()