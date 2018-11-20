from object_tracker import ImageObject, ObjectType

import operator

class Scene():
    i = 0

    DIST_ALLOWED_SQ = 500
    UNSEEN_ALLOWED = 3

    def __init__(self):
        self.objects = {}

    @staticmethod
    def get_id():
        i = Scene.i
        Scene.i += 1
        return i

    def add_object(self, new_obj: ImageObject):
        for i, obj in self.objects.items():
            obj.unseen += 1

        contain_list = {}
        for i, obj in self.objects.items():
            #if(new_obj.distance_square_from(obj) < Scene.DIST_ALLOWED_SQ):
            if(obj.contains(new_obj) and new_obj.distance_square_from(obj) < Scene.DIST_ALLOWED_SQ):
                contain_list[i] = new_obj.distance_square_from(obj)

        if len(contain_list):
            min_dist_id = min(contain_list.items(), key = operator.itemgetter(1))[0]
            self.objects[min_dist_id].update_state(new_obj.contour, new_obj.roi, new_obj.type)
        else:
            new_obj.id = Scene.get_id()
            self.objects[new_obj.id] = new_obj


        expired_list = []
        for i, obj in self.objects.items():
            if(obj.unseen > Scene.UNSEEN_ALLOWED):
                expired_list.append(i)

        for i in expired_list:    
            del self.objects[i]