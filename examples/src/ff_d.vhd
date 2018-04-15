library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity ff_d is
	port (
		clk : in STD_LOGIC;
		rst : in STD_LOGIC;

		d : in STD_LOGIC;

		q : out STD_LOGIC := '0'
	);
end ff_d;

architecture ff_d_arch of ff_d is
begin
	process (clk) is
	begin
	if rising_edge(clk) then
		if rst = '1' then
			q <= '0';
		else
			q <= d;
		end if;
	end if;
	end process;
end ff_d_arch;
