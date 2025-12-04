Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}

function onDateUpdate(){
    const date1=new Date(document.querySelector("#id_checkin").value)
    const date2=new Date(document.querySelector("#id_checkout").value)
    document.querySelector("#total-days").innerHTML=(date2.getTime() - date1.getTime())/(1000*3600*24)

}

document.querySelector("#id_checkout").addEventListener("change",(e)=>{
    onDateUpdate()
    document.querySelector("#id_guests").focus()
    
})
// document.querySelector("#id_checkin").addEventListener("change",(e)=>{
//     const checkout=document.querySelector("#id_checkout")

//     const tomorrow=new Date(e.target.value).addDays(1).toISOString().split('T')[0]
//     if(e.target.value>checkout.value){
//         checkout.setAttribute("value",tomorrow)
        
//     }
//     onDateUpdate()
//     checkout.setAttribute("min",tomorrow)
//     checkout.focus()
// })


function searchRoom() {
    const query = document.getElementById('roomSearch').value.toLowerCase();
    const rooms = document.querySelectorAll('.room');
    rooms.forEach(room => {
        const text = room.textContent.toLowerCase();
        if (text.includes(query)) {
            room.style.display = '';
        } else {
            room.style.display = 'none';
        }
    });
}
