import unittest

class TestParseVCD(unittest.TestCase):
    def test_read_file(self):
        vcd=vcd_reader('divider.vcd')
        self.assertEqual(len(vcd.signal_symbol_dict),23)
        self.assertEqual(vcd.signal_symbol_dict['/clk'],'!')
        self.assertEqual(vcd.signal_symbol_dict['/dut/divisor[16:0]'],'/')
        self.assertEqual(vcd.signal_symbol_dict['/i'],'"')
        self.assertEqual(vcd.end_time,250000000)
        self.assertequal(len(vcd.transitions_dict['!'][0]),51)
        self.assertEqual(vcd.symbols(['/clk']),{'/clk':'!'})
        self.assertEqual(vcd.symbols(['/clk','/dut/clk']),{'/clk': '!', '/dut/clk': ','})
    def test_symbols(self,array_of_names):
        self.assertEqual(vcd.symbols(['/clk']),{'/clk':'!'})
        self.assertEqual(vcd.symbols(['/clk','/dut/clk']),{'/clk': '!', '/dut/clk': ','})
    def test_time_query_transitions(self):
        dict_clk={'!': [[5000000,   10000000,   15000000,   20000000,   25000000,   30000000,   35000000,   40000000,   45000000,   50000000,   55000000,   60000000,   65000000,   70000000,   75000000,   80000000,   85000000,   90000000,   95000000],  ['1',   '0',   '1',   '0',   '1',   '0',   '1',   '0',   '1',   '0',   '1',   '0',   '1',   '0',   '1',   '0',   '1',   '0',   '1']]}
        self.assertEqual(vcd.time_query_transitions(['/clk'],100,100000000), dict_clk)
    def test_value_at(self):
        pass
    
