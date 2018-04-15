library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity bidir is
	port (
		dir : in STD_LOGIC;

		a : inout STD_LOGIC;
		b : inout STD_LOGIC
	);
end bidir;

architecture bidir_arch of bidir is
	signal s_a_out : STD_LOGIC := 'Z';
	signal s_b_out : STD_LOGIC := 'Z';
begin
	s_a_out <= b when dir = '0';
	s_b_out <= a when dir = '1';

	a <= s_a_out when dir = '0' else 'Z';
	b <= s_b_out when dir = '1' else 'Z';
end bidir_arch;
