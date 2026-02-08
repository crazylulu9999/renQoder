import comtypes.client as cc
import ctypes

class TaskbarController:
    """
    Windows Taskbar Progress 연동 클래스 (ITaskbarList3 사용)
    """
    # 윈도우 API 상수 (상태값)
    TBPF_NOPROGRESS = 0
    TBPF_INDETERMINATE = 1
    TBPF_NORMAL = 2      # 초록색 (진행 중)
    TBPF_ERROR = 4       # 빨간색 (에러)
    TBPF_PAUSED = 8      # 노란색 (일시정지)

    def __init__(self, window_id):
        """
        Args:
            window_id: 윈도우 핸들 (int) - CustomTkinter의 winfo_id() 값
        """
        self.hwnd = int(window_id)
        self.tbl = None
        try:
            # ITaskbarList3 인터페이스 생성
            # CLSID_TaskbarList = {56FDF344-FD6D-11d0-958A-006097C9A090}
            self.tbl = cc.CreateObject("{56FDF344-FD6D-11d0-958A-006097C9A090}")
            # HrInit 호출이 필요할 수 있음 (일부 환경)
            if hasattr(self.tbl, 'HrInit'):
                self.tbl.HrInit()
        except Exception as e:
            print(f"TaskbarController init error: {e}")
            self.tbl = None

    def set_value(self, value, total=100):
        """진행률 업데이트 (초록색)"""
        if not self.tbl: return
        try:
            self.tbl.SetProgressState(self.hwnd, self.TBPF_NORMAL)
            self.tbl.SetProgressValue(self.hwnd, int(value), int(total))
        except: pass

    def set_error(self):
        """에러 상태 표시 (빨간색)"""
        if not self.tbl: return
        try:
            self.tbl.SetProgressState(self.hwnd, self.TBPF_ERROR)
            self.tbl.SetProgressValue(self.hwnd, 100, 100)
        except: pass

    def reset(self):
        """진행 표시 제거"""
        if not self.tbl: return
        try:
            self.tbl.SetProgressState(self.hwnd, self.TBPF_NOPROGRESS)
        except: pass

    def stop(self):
        """reset의 별칭"""
        self.reset()
