//public module

pub fn outer_module_function(x: i32) -> i32 {
	if x > 0{
		if x == 1{
			return 1;
		}
		return x + outer_module_function(x-1)
	}else { 
		return x;
	}
	
}
