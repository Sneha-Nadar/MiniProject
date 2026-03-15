async function startLive(){

await fetch("/recognize-live",{method:"POST"})

alert("Camera started. Please face the camera.")

}


async function uploadVideo(){

let file = document.getElementById("videoFile").files[0]

let form = new FormData()

form.append("file",file)

await fetch("/upload-video",{method:"POST",body:form})

alert("Video uploaded. Processing started.")

}


async function loadAttendance(){

const res = await fetch("/attendance")

const data = await res.json()

let table = document.getElementById("attendanceTable")

table.innerHTML=""

data.forEach(row => {

table.innerHTML += `
<tr class="border-b border-gray-700">
<td class="p-3">${row.Name}</td>
<td class="p-3">${row.Date}</td>
<td class="p-3">${row.Time}</td>
</tr>
`

})

document.getElementById("detectedCount").innerText = data.length

}


async function loadStudents(){

const res = await fetch("/students")

const data = await res.json()

document.getElementById("studentsCount").innerText = data.total_students

}


setInterval(loadAttendance,2000)

loadStudents()