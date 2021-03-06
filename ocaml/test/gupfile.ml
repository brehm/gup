open Batteries
open OUnit2
open Gup.Gupfile
open Gup
open Gup.Path

let possible_gup_files path =
	let path = PathAssertions.absolute path in
	List.of_enum (possible_builders (ConcreteBase._cast path))

let print_builder (candidate, gupfile, target) =
	let guppath = Absolute.to_string (candidate#guppath gupfile) in
	let target = Relative.to_string target in
	Printf.sprintf2 "%s (%s)" guppath target

let print_str_list lst = "[ " ^ (lst |> String.concat "\n") ^ " ]"
let custom_printf fn obj = Printf.sprintf2 "%a" fn obj
let lift_compare m f a b = m (f a) (f b)
let eq cmp a b = (cmp a b) = 0
let compare_gupfile =
	let compare_rule = lift_compare String.compare (fun r -> r#text) in
	let compare_rules = lift_compare (List.compare compare_rule) (fun r -> r#rules) in
	let compare_string_and_rules = (Tuple2.compare ~cmp1:String.compare ~cmp2:compare_rules) in
	eq @@ List.compare compare_string_and_rules

let suite = "Gupfile" >:::
[
	"gupfile search paths" >:: (fun _ ->
		assert_equal
			~printer: print_str_list
			[
				"/a/b/c/d/e.gup (e)";
				"/a/b/c/d/gup/e.gup (e)";
				"/a/b/c/gup/d/e.gup (e)";
				"/a/b/gup/c/d/e.gup (e)";
				"/a/gup/b/c/d/e.gup (e)";
				"/gup/a/b/c/d/e.gup (e)";
				"/a/b/c/d/Gupfile (e)";
				"/a/b/c/d/gup/Gupfile (e)";
				"/a/b/c/gup/d/Gupfile (e)";
				"/a/b/gup/c/d/Gupfile (e)";
				"/a/gup/b/c/d/Gupfile (e)";
				"/gup/a/b/c/d/Gupfile (e)";
				"/a/b/c/Gupfile (d/e)";
				"/a/b/c/gup/Gupfile (d/e)";
				"/a/b/gup/c/Gupfile (d/e)";
				"/a/gup/b/c/Gupfile (d/e)";
				"/gup/a/b/c/Gupfile (d/e)";
				"/a/b/Gupfile (c/d/e)";
				"/a/b/gup/Gupfile (c/d/e)";
				"/a/gup/b/Gupfile (c/d/e)";
				"/gup/a/b/Gupfile (c/d/e)";
				"/a/Gupfile (b/c/d/e)";
				"/a/gup/Gupfile (b/c/d/e)";
				"/gup/a/Gupfile (b/c/d/e)";
				"/Gupfile (a/b/c/d/e)";
				"/gup/Gupfile (a/b/c/d/e)"
			]
			(possible_gup_files("/a/b/c/d/e") |> List.map print_builder)
		;

		assert_equal
			~printer: print_str_list
			[
				"/x/y/somefile.gup (somefile)";
				"/x/y/gup/somefile.gup (somefile)";
				"/x/gup/y/somefile.gup (somefile)"
			]
			(possible_gup_files "/x/y/somefile" |> List.take 3 |> List.map print_builder)
		;
	);

	"gupfile parsing" >:: (fun _ ->
		assert_equal
		~printer: (custom_printf print_gupfile)
		~cmp: (compare_gupfile)
		[
			("foo.gup", new match_rules [
				new match_rule "foo1";
				new match_rule "foo2"]
			);
			("bar.gup", new match_rules [
				new match_rule "bar1";
				new match_rule "bar2"]
			)
		]
		(parse_gupfile @@ IO.input_string (
			String.concat "\n" [
				"foo.gup:";
				" foo1";
				"# comment";
				"";
				"\t foo2";
				"# comment";
				"ignoreme:";
				"bar.gup :";
				" bar1\t ";
				"    bar2";
			])
		)
	);

	"rule parsing" >:: (fun _ ->
		assert_equal ~printer:identity "^[^/]*$"         (regexp_of_rule "*");
		assert_equal ~printer:identity "^.*$"            (regexp_of_rule "**");
		assert_equal ~printer:identity "^foo.*bar[^/]*$" (regexp_of_rule "foo**bar*");
	);

	"extracting extant targets from rules" >:: (fun _ ->
		let assert_equal = assert_equal ~printer: print_str_list in
		let gen_targets rules ?(dir="") files =
			let rules = new match_rules (
					rules |> List.map (fun r -> new match_rule r)
			) in
			rules#definite_targets_in dir (Array.of_list files)
				|> List.of_enum
		in

		assert_equal [ "file1" ] (gen_targets ["file1"; "*.html"] []);
		assert_equal [ "file1"; "index.html" ] (gen_targets ["file1"; "*.html"] ["index.html"]);
		assert_equal [ "file2" ] (gen_targets ["file1"; "dir*/file2"] ~dir:"dir1" []);
	);
]
