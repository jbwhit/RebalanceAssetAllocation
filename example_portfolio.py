import PortfolioAnalysis
from PortfolioAnalysis import Portfolio

example_portfolio = Portfolio()
example_portfolio.get_ideal_allocation('ideal-allocation.txt')
example_portfolio.get_account_details(['scottrade-main.txt', 'scottrade-roth.txt'])
example_portfolio.get_stock_prices()

example_portfolio.get_core_total()
example_portfolio.get_current_allocation()

example_portfolio.summary()
example_portfolio.get_recommendations()
example_portfolio.detailed_summary()

#Send email crontab / python


