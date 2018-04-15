library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity hiz_out is
	port (
		oe : in STD_LOGIC;

		a : in STD_LOGIC;
		av : in STD_LOGIC_VECTOR (1 downto 0);

		b : inout STD_LOGIC;
		bv : inout STD_LOGIC_VECTOR (1 downto 0)
	);
end hiz_out;

architecture hiz_out_arch of hiz_out is
begin
	b <= a when oe = '0' else 'Z';
	bv <= av when oe = '0' else (others => 'Z');
end hiz_out_arch;
