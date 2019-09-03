service xoj {
    string checker(1:string script_path, 2:string ip, 3:i32 port),
    string attack(1:string script_path,2:string ip, 3:i32 port, 4:string arg),
}