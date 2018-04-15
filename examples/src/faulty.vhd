library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity faulty is
	port (
		a : in STD_LOGIC;
		z : out STD_LOGIC
	);
end faulty;

architecture faulty_arch of faulty is
begin
	z <= a;
end faulty_arch;
