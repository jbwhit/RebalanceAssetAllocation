#!/usr/bin/env python

import numpy as np
from pandas.io.data import get_quote_yahoo
import json
import locale
locale.setlocale(locale.LC_ALL, '')


class Portfolio(object):
    def __init__(self):
        self.ideal_allocation = {}
        self.stocks_owned = {}
        self.class_total = {}
        self.cash = 0.0
        self.classification = {}
        self.current_asset_percentages = []
        self.core_total = 0.0
        self.total = 0.0
        self.tolerance = 3.5  # percentage off ideal before recommended action
        pass

    def get_ideal_allocation(self, infile):
        """Reads in file of ideal portfolio allocation.
           Use 1-word (no spaces) for asset class.
           "tolerance" is a special word which gives the tolerance level
            before a rebalance is recommended."""
        with open(infile, 'r') as file_handle:
            for line in file_handle:
                if line.split()[0] == "tolerance":
                    self.tolerance = float(line.split()[1])
                else:
                    self.ideal_allocation[line.split()[0]] = float(line.split()[1])
                    self.class_total[line.split()[0]] = 0.0

    def parse_ideal_allocation(self, infile):
        """Reads in json formatted file of the ideal portfolio
            allocation."""
        with open(infile, 'r') as file_handle:
            allocation_dict = json.load(file_handle)

        for key in allocation_dict:
            if key == "tolerance":
                self.tolerance = allocation_dict[key]
            else:
                self.ideal_allocation[key] = float(allocation_dict[key])
                self.class_total[key] = 0.0
        pass

    def get_account_details(self, infiles):
        for infile in infiles:
            with open(infile, 'r') as file_handle:
                for line in file_handle:
                    name = line.split()[0]
                    if name == 'CASH':
                        self.cash += float(line.split()[1].strip("$"))
                    else:
                        if name not in self.stocks_owned:
                            self.stocks_owned[name] = {}
                            self.stocks_owned[name]['shares'] = 0.0
                            self.stocks_owned[name]['shares'] += float(line.split()[1])
                            self.stocks_owned[name]['assetClass'] = line.split()[2]
                        else:
                            self.stocks_owned[name]['shares'] += float(line.split()[1])
                            self.stocks_owned[name]['assetClass'] = line.split()[2]

    def parse_account_details(self, webdict):
        for name in webdict:
            if name == 'CASH':
                self.cash += webdict[name]
            else:
                if name not in self.stocks_owned:
                    self.stocks_owned[name] = {}
                    self.stocks_owned[name]['shares'] = 0.0
                    self.stocks_owned[name]['shares'] += webdict[name]['shares']
                    self.stocks_owned[name]['assetClass'] = webdict[name]['assetClass']
                else:
                    self.stocks_owned[name]['shares'] += webdict[name]['shares']
                    self.stocks_owned[name]['assetClass'] = webdict[name]['assetClass']

    def get_stock_prices(self):
        dataframe = get_quote_yahoo([stock for stock in self.stocks_owned])
        for stock in self.stocks_owned:
            self.stocks_owned[stock]['price'] = dataframe.ix[stock]['last']

    def get_core_total(self):
        self.core_total = 0.0
        self.total = 0.0
        self.core_total += self.cash
        self.total += self.cash
        for stock in self.stocks_owned:
            temp_amount = self.stocks_owned[stock]['price'] * self.stocks_owned[stock]['shares']
            if self.stocks_owned[stock]['assetClass'] in self.ideal_allocation:
                self.core_total += temp_amount
                self.class_total[self.stocks_owned[stock]['assetClass']] += temp_amount
                self.total += temp_amount
            else:
                self.total += temp_amount
        pass

    def get_current_allocation(self):
        """Remember same stock can't have two assetClasses."""
        for stock in self.stocks_owned:
            if self.stocks_owned[stock]['assetClass'] in self.ideal_allocation:
                temp_asset = self.stocks_owned[stock]['assetClass']
                self.current_asset_percentages.append(
                    (stock,
                        self.class_total[temp_asset] / self.core_total * 100. - self.ideal_allocation[temp_asset],
                        temp_asset))

    def get_recommendations(self):
        """Print recommendations."""
        print "Recommended actions:"
        for st, perc, asset in sorted(self.current_asset_percentages, key=lambda x: np.abs(x[1]), reverse=True):
            shares = round(self.core_total * perc / 100. / self.stocks_owned[st]['price'], 0)
            if np.abs(perc) >= self.tolerance:
                if shares > 0:
                    print "Sell:", int(np.abs(shares)), st, asset, round(perc, 1)
                if shares < 0:
                    print "Buy:", int(np.abs(shares)), st, asset, round(perc, 1)
            else:
                print "W/in tol:",
                if shares > 0.0:
                    print "Sell", int(np.abs(shares)), st, asset, round(perc, 1)
                else:
                    print "Buy", int(np.abs(shares)), st, asset, round(perc, 1)
        pass

    def push_recommendations(self, return_string=""):
        """Pushover recommendations."""
        priority = 0
        return_string = '\n'.join([return_string, "Recommended actions:", '\n'])
        for st, perc, asset in sorted(self.current_asset_percentages, key=lambda x: x[1], reverse=True):
            shares = round(self.core_total * perc / 100. / self.stocks_owned[st]['price'], 0)
            if np.abs(perc) >= self.tolerance:
                priority = 1
                if shares > 0:
                    return_string = ' '.join([return_string,
                                              "Sell:",
                                              str(int(np.abs(shares))),
                                              str(st), str(asset),
                                              str(round(perc, 1)),
                                              '\n'])
                if shares < 0:
                    return_string = ' '.join([return_string,
                                              "Buy:",
                                              str(int(np.abs(shares))),
                                              str(st),
                                              str(asset),
                                              str(round(perc, 1)),
                                              '\n'])
            else:
                return_string = ' '.join([return_string, "W/in tol:", ])
                if shares > 0.0:
                    return_string = ' '.join([return_string,
                                              "Sell",
                                              str(int(np.abs(shares))),
                                              str(st),
                                              str(asset),
                                              str(round(perc, 1)),
                                              '\n'])
                else:
                    return_string = ' '.join([return_string,
                                              "Buy",
                                              str(int(np.abs(shares))),
                                              str(st),
                                              str(asset),
                                              str(round(perc, 1)),
                                              '\n'])
        return return_string, priority

    def get_summary(self):
        print "Cash:", locale.currency(self.cash, grouping=True)
        print "Core Total:", locale.currency(self.core_total, grouping=True)
        print "Total:", locale.currency(self.total, grouping=True)
        pass

    def push_summary(self):
        """Pushover summary."""
        return_string = ""
        return_string = ' '.join([return_string,
                                 "Cash:",
                                 locale.currency(self.cash, grouping=True),
                                 "\n"])
        return_string = ' '.join([return_string,
                                 "Core Total:",
                                 locale.currency(self.core_total, grouping=True),
                                 "\n"])
        return_string = ' '.join([return_string,
                                 "Total:",
                                 locale.currency(self.total, grouping=True),
                                 "\n"])
        return return_string

    def push_full_recommendations(self):
        """Both overall summary and recommendations."""
        summary = self.push_summary()
        return self.push_recommendations(summary)

    def detailed_summary(self):
        for stock in self.stocks_owned:
            print stock, locale.currency(self.stocks_owned[stock]['price'] * self.stocks_owned[stock]['shares'],
                                         grouping=True)
        pass
