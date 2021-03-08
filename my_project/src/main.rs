mod outer_module;
use outer_module::outer_module_function;

fn another_function(x: i32, y: i32) {
    println!("{}",x);
    println!("{}",y);
}

fn main() {
	// comment
    let mut a = 12;
    println!("a is {}", a);
    
    another_function(1,2);
    
    while a < 14 {
    	println!(".");
    	a += 1;
    }
    
    println!("{}", outer_module_function(3));
}
