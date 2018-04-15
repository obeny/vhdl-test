library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity and_gate is
	port (
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC
	);
end and_gate;

architecture and_gate_arch of and_gate is
begin
	z <= a and b;
end and_gate_arch;
