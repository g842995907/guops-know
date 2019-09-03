
var StatusConstant = {};
var constant = {
    User: {
        Status: {
            NORMAL: 1,
            REGISTER: 2,
            PASS: 3,
            EXPIRED: 4,
            Disabled:5,
            }
        },
    Applided: {
      Status: {
        INVITATION: 0,
        HASINVITATION: 1,
        JOINED: 2,
      }
    }
}
$.extend(true, StatusConstant, constant);