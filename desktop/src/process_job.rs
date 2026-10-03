//! O último handle fechado encerra os processos que este aplicativo iniciou.
#[cfg(windows)]
use std::os::windows::io::AsRawHandle;
#[cfg(windows)]
use windows_sys::Win32::{Foundation::{CloseHandle,HANDLE},System::JobObjects::{CreateJobObjectW,SetInformationJobObject,AssignProcessToJobObject,JOBOBJECT_EXTENDED_LIMIT_INFORMATION,JobObjectExtendedLimitInformation,JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE}};

#[cfg(windows)]
pub struct ProcessJob(HANDLE);
#[cfg(windows)]
unsafe impl Send for ProcessJob {}
#[cfg(windows)]
impl ProcessJob {
    pub fn attach(child: &std::process::Child) -> Result<Self, String> {
        unsafe {
            let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
            if handle.is_null() { return Err("Não foi possível criar o grupo de processos local".into()); }
            let job = Self(handle);
            let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            if SetInformationJobObject(handle, JobObjectExtendedLimitInformation, &info as *const _ as *const _, std::mem::size_of_val(&info) as u32) == 0
                || AssignProcessToJobObject(handle, child.as_raw_handle() as HANDLE) == 0 {
                return Err("Não foi possível vincular o backend ao encerramento do aplicativo".into());
            }
            Ok(job)
        }
    }
}
#[cfg(windows)]
impl Drop for ProcessJob { fn drop(&mut self) { unsafe { CloseHandle(self.0); } } }
#[cfg(not(windows))]
pub struct ProcessJob;
#[cfg(not(windows))]
impl ProcessJob { pub fn attach(_: &std::process::Child) -> Result<Self,String> {Ok(Self)} }
