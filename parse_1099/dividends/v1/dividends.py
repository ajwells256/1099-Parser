import re
import locale

from ..dividends_interface import DividendsInterface

class Dividends(DividendsInterface):

    columns = ["description", "sold_date", "quantity", "proceeds", "acquired_date", "cost", "wash_dividends_loss", "gain_loss"]

    _comma_number_pat = "\d?\d?\d(,\d\d\d)*"
    _date_pat = "\d\d\/\d\d\/\d\d"

    _date_pattern = re.compile(f"^{_date_pat}$")
    _quantity_pattern = re.compile(f"^{_comma_number_pat}\.\d+$")
    _money_pattern = re.compile(f"^\-?{_comma_number_pat}\.\d\d$")


    def __init__(self, data: list):
        super().__init__(data, self.columns)
        assert(isinstance(data, list))
        # == Columns ==
        assert(isinstance(data[0], str)) # descripion
        assert(Dividends._date_pattern.match(data[1])) # sold_date
        assert(Dividends._quantity_pattern.match(data[2])) # quantity
        assert(re.match(f"^\-?{self._comma_number_pat}\.\d\d( [NG])?$", data[3])) # proceeds
        assert(Dividends._date_pattern.match(data[4])) # acquired_date
        assert(Dividends._money_pattern.match(data[5])) # cost
        assert(re.match(f"^(\-?{self._comma_number_pat}\.\d\d [W])?$", data[6])) # wash_dividends_loss
        assert(Dividends._money_pattern.match(data[7])) # gain_loss
    

    @staticmethod
    def parse(raw_data: list) -> list:
        transx = []
        assert(isinstance(raw_data, list))
        if not raw_data: return transx  # empty list

        desc = raw_data[0].strip()

        shift = 1
        while shift < len(raw_data) - 7:
            multi = re.match(f"^(?P<cnt>{Dividends._comma_number_pat}) transactions for (?P<sold_date>{Dividends._date_pat}).", raw_data[shift])
            if multi:
                # Multiple entries
                cnt = locale.atoi(multi.group("cnt"))
                sold_date = multi.group("sold_date")

                # print(f"{cnt} transactions sold on {sold_date}")
            elif Dividends._date_pattern.match(raw_data[shift]):
                cnt = 1
                sold_date = raw_data[shift]
            else:
                shift += 1
                continue


            n = 0
            while n < cnt:
                shift += 1
                filtered = []
                shift_extra = 0

                # quantity
                if not Dividends._quantity_pattern.match(raw_data[shift+shift_extra]):
                    if cnt > 1: continue
                    else: break
                filtered.append(raw_data[shift+shift_extra])

                # proceeds
                if not Dividends._money_pattern.match(raw_data[shift+shift_extra+1]):
                    if cnt > 1: continue
                    else: break
                filtered.append(raw_data[shift+shift_extra+1])
                # Gross Net - Potential Extra character
                gross_net = raw_data[shift+shift_extra+2]
                if gross_net == 'N' or gross_net == 'G':
                    filtered[1] += " " + gross_net
                    shift_extra += 1

                # date_acquired
                if not Dividends._date_pattern.match(raw_data[shift+shift_extra+2]):
                    if cnt > 1: continue
                    else: break
                filtered.append(raw_data[shift+shift_extra+2])

                # cost
                if not Dividends._money_pattern.match(raw_data[shift+shift_extra+3]): 
                    if cnt > 1: continue
                    else: break
                filtered.append(raw_data[shift+shift_extra+3])

                # wash_dividends_loss
                if raw_data[shift+shift_extra+4] == "...":
                    filtered.append("")

                elif Dividends._money_pattern.match(raw_data[shift+shift_extra+4]):
                    filtered.append(raw_data[shift+shift_extra+4])
                    # disallowed - Potential Extra character
                    if raw_data[shift+shift_extra+5] == "W":
                        filtered[4] += " " + raw_data[shift+shift_extra+5]
                        shift_extra += 1

                else:
                    if cnt > 1: continue
                    else: break
                
                # gain_loss
                if not Dividends._money_pattern.match(raw_data[shift+shift_extra+5]):
                    if cnt > 1: continue
                    else: break
                filtered.append(raw_data[shift+shift_extra+5])
                
                if cnt > 1:
                    # Count check
                    raw_nth = raw_data[shift+shift_extra+6]
                    nth_i = 1
                    def getNthData():
                        return re.match(f"^(?P<nth>{Dividends._comma_number_pat}) of (?P<total>{Dividends._comma_number_pat})", raw_nth)
                    nth_data = getNthData()
                    while not nth_data:
                        shift_extra += 1
                        raw_nth += " " + raw_data[shift+shift_extra+6]
                        if nth_i >= 3:
                            raise Exception(f"Error while parsing...\n"
                                            f"  {desc}\n"
                                            f"  {sold_date} {filtered}")
                        nth_i += 1
                        nth_data = getNthData()

                    assert(locale.atoi(nth_data.group("nth")) == n + 1)
                    assert(locale.atoi(nth_data.group("total")) == cnt)
                
                # Add sold_date to the front
                filtered.insert(0, sold_date)
                filtered.insert(0, desc)
                transx.append(Dividends(filtered))
                # print(filtered)

                shift += shift_extra + 6
                n += 1
                # Clean
                del filtered

        return transx
