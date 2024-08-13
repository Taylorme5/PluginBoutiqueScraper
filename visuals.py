import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from typing import Union

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def product_jointplot(products_df, _x, _y, _z, title):
    """
    Takes in the products dataframe and returns a joint plot of price x to y using JointGrid.
    :param products_df: product dataframe
    """
    palette = sns.color_palette("blend:#103,#0F0", as_cmap=True)
    g = sns.JointGrid(height=8, ratio=2, space=.05, data=products_df, x=_x,
                      y=_y, hue=_z, palette=palette)

    g.plot_joint(sns.scatterplot, alpha=0.5, linewidth=.7, palette=palette)
    g.plot_marginals(sns.histplot, kde=True, bins=20)

    sns.move_legend(g.ax_joint, "upper left", bbox_to_anchor=(.20, .90), title=_z)
    g.ax_joint.grid(True)
    g.fig.suptitle(title, fontsize=16)

    plt.show()


@app.get("/top_manufacturers")
def top_manufacturers(manufacturer_df, determinant, n):
    """
    Returns a dataframe of the top n most popular manufacturers.
    Review count is used as a proxy for popularity.
    :param manufacturer_df: manufacturer dataframe
    :param determinant: what determines what puts a manufacturer at the top
    :param n: desired number of manufacturers
    """
    sorted_manufacturers = manufacturer_df.sort_values(by=determinant, ascending=False)
    top_n_manufacturers = sorted_manufacturers.head(n)
    return top_n_manufacturers


def manufacturer_df_to_product_df(manufacturer_df):
    """Converts the products attribute of a manufacturer_df to a products_df
        :param manufacturer_df = manufacturer data frame
    """
    product_data = []

    for _, manufacturer in manufacturer_df.iterrows():
        products_data = manufacturer['products']

        for product in products_data:
            name = product['name']
            manufacturer_name = manufacturer['manufacturer']
            attributes = product['attributes']
            id_ = attributes.get('id', None)
            categories = attributes.get('categories', None)
            sell_price = attributes.get('sell_price($)', None)
            list_price = attributes.get('list_price($)', None)
            on_sale = attributes.get('on_sale', None)
            review_count = attributes.get('review_count', None)
            rating = attributes.get('rating', None)

            product_data.append({'name': name, 'id': id_, 'manufacturer': manufacturer_name, 'categories': categories,
                                 'sell_price($)': float(sell_price), 'list_price($)': float(list_price),
                                 'on_sale': on_sale, 'review_count': review_count, 'rating': rating})
    product_df = pd.DataFrame(product_data)
    product_df.sort_values('manufacturer')
    return product_df


def products_PairGrid(products_df):
    """
    Takes in the products dataframe and returns a pair grid of most interesting attributes.
    :param products_df: product dataframe
    """
    # plt.figure(figsize=(10, 10))
    g = sns.PairGrid(products_df, vars=['discount', 'sell_price($)', 'list_price($)', 'rating', 'review_count'])
    g.map(sns.scatterplot, alpha=0.4, hue='manufacturer', data=products_df, legend=True)
    g.fig.suptitle('Products Attributes Scatter Plots', )
    plt.show()


def manufacturer_violin_plot(manufacturer_df, determinant, n, title='Price Distribution of Top Manufacturers',
                             split=False):
    """
    Creates a violin plot that displays a distribution of product ratings for the top 8 manufacturers.
    The products are derived from mn
    :param manufacturer_df: manufacturer dataframe
    :param determinant: what to order the top manufacturers by
    :param n: desired number of manufacturers in the table
    :param title: title of the plot
    :param split: whether a split violin plot is desired
    """
    top_manufacturers_df = top_manufacturers(manufacturer_df, determinant, n)
    products_df = manufacturer_df_to_product_df(top_manufacturers_df)

    if not split:
        plt.figure(figsize=(10, 10))
        plot = sns.violinplot(y='manufacturer', x='list_price($)', data=products_df,
                              palette=sns.color_palette(), inner='quart', split=False,
                              hue='manufacturer', legend=True)
    else:
        plt.figure(figsize=(10, 10))
        plot = sns.violinplot(y='manufacturer', x='sell_price($)', data=products_df,
                              inner='quart', split=True, gap=0.1,
                              hue='on_sale', legend=True)
    plot.set_title(title)
    plt.yticks(ticks=range(len(top_manufacturers_df)),
               labels=top_manufacturers_df['manufacturer'] + '\n' +
                      '(product count: ' + top_manufacturers_df['product_count'].astype(str) + '\n' +
                      'rating: ' + top_manufacturers_df['rating'].astype(str) + '\n' +
                      'review_count: ' + top_manufacturers_df['review_count'].astype(str) + ')')
    plt.ylabel('Manufacturer')
    plt.xlabel('Sell price')
    plt.tight_layout()
    plt.show()


def manufacturer_rating_distribution(manufacturer_df, determinant, n, title='Rating Distribution of Top Manufacturers'):
    """
    Plots a multiple bar graph showing the distribution of product ratings for each manufacturer.
    :param manufacturer_df: manufacturer dataframe
    :param determinant: what to order the top manufacturers by
    :param n: desired number of manufacturers in the table
    :param title: title of the plot
    """
    top_manufacturers_df = top_manufacturers(manufacturer_df, determinant, n)
    products_df = manufacturer_df_to_product_df(top_manufacturers_df)

    g = sns.FacetGrid(products_df, col="manufacturer", col_wrap=4, margin_titles=True, sharex=False, sharey=False)
    g.map(sns.histplot, "rating", kde=True, bins=[0, 1, 2, 3, 4, 5], discrete=True)

    g.set_axis_labels("Rating", "Count")
    g.set_titles(col_template="{col_name}")

    plt.subplots_adjust(top=0.9)
    g.fig.suptitle(title)
    plt.show()


def main():
    products_df = pd.read_json("www.pluginboutique.com-products.jsonl", lines=True, encoding='utf-8')
    manufacturers_df = pd.read_json("www.pluginboutique.com-manufacturers.jsonl", lines=True, encoding='utf-8')

    # PairGrid
    products_PairGrid(products_df)

    # product joint plots
    # FabFilter Pro-Q 3, "/Effects/EQ", 119.0        Scaler 2 Upgrade from Scaler 1
    product_jointplot(products_df, 'rating', 'review_count', 'discount', 'Rating/Review Count/Discount')
    # Trend
    product_jointplot(products_df, 'discount', 'list_price($)', 'rating', 'Discount/List Price/Rating')

    # price distribution violin plots
    manufacturer_violin_plot(manufacturers_df, 'product_count', 10,
                             'Price Distribution of Top Manufacturers by Product Count', split=True)
    manufacturer_violin_plot(manufacturers_df, 'review_count', 10,
                             'Price Distribution of Top Manufacturers by Popularity', split=True)
    manufacturer_violin_plot(manufacturers_df, 'rating', 10,
                             'Price Distribution of Top Rated Manufacturers', split=True)
    manufacturer_violin_plot(manufacturers_df, 'reliability', 10,
                             'Price Distribution of Most Reliable Manufacturers', split=True)

    # rating distribution histograms
    manufacturer_rating_distribution(manufacturers_df, 'product_count', 12,
                                     'Rating Distribution of Top Manufacturers by Product Count')
    manufacturer_rating_distribution(manufacturers_df, 'review_count', 12,
                                     'Rating Distribution of Top Manufacturers by Popularity (review count)')
    manufacturer_rating_distribution(manufacturers_df, 'rating', 12,
                                     'Rating Distribution of Top Rated Manufacturers')
    manufacturer_rating_distribution(manufacturers_df, 'reliability', 12,
                                     'Rating Distribution of Most Reliable Manufacturers')


if __name__ == '__main__':
    main()
