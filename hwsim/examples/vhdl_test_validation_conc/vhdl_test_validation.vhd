library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity vhdl_test_validation is
	port (
		-- component selector
		comp : in STD_LOGIC_VECTOR (0 to 2);
		
		-- concurrent inputs
		s : in STD_LOGIC;
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC;

		led : out STD_LOGIC
	);
end vhdl_test_validation;

architecture vhdl_test_validation_arch of vhdl_test_validation is
	component and_gate
	port (
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC
	);
	end component;

	component xor_gate
	port (
		a : in STD_LOGIC;
		b : in STD_LOGIC;
		z : out STD_LOGIC
	);
	end component;
	
	component mux is
	port (
		s : in STD_LOGIC;
		a : in STD_LOGIC_VECTOR (0 to 3);
		b : in STD_LOGIC_VECTOR (0 to 3);
		z : out STD_LOGIC_VECTOR (0 to 3)
	);
	end component;

	signal s_a : STD_LOGIC;
	signal s_b : STD_LOGIC;
	signal s_and_gate_z : STD_LOGIC;
	signal s_xor_gate_z : STD_LOGIC;
	signal s_mux_z : STD_LOGIC_VECTOR (0 to 3);
	signal s_z : STD_LOGIC;

begin
	u_and_gate: and_gate
	port map(
		a => s_a,
		b => s_b,
		z => s_and_gate_z
	);

	u_xor_gate: xor_gate
	port map(
		a => s_a,
		b => s_b,
		z => s_xor_gate_z
	);

	u_mux: mux
	port map(
		s => s,
		a => s_a & "000",
		b => s_b & "000",
		z => s_mux_z
	);

	s_a <= a;
	s_b <= b;
	
	with comp select s_z <=
		s_and_gate_z when "000",
		s_xor_gate_z when "001",
		s_mux_z(0) when "010",
		'0' when "011",
		'0' when "100",
		'0' when "101",
		'0' when "110",
		'0' when "111";

	z <= s_z;
	led <= not s_z;
end vhdl_test_validation_arch;
