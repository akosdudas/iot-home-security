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
            self.objects[min_dist_id].update_state(new_obj)
        else:
            new_obj.id = Scene.get_id()
            self.objects[new_obj.id] = new_obj


        expired_list = []
        for i, obj in self.objects.items():
            if(obj.unseen > Scene.UNSEEN_ALLOWED):
                expired_list.append(i)

        for i in expired_list:    
            del self.objects[i]

    def update_objects(self, detected_objects: list):
        detected_objects_copy = detected_objects.copy()
        # Increase the age of all historical objects in the scene
        for i, obj in self.objects.items():
            obj.unseen += 1
        
        # Try to find one to one matches for the existing objects
        match_canditates = []
        for i, obj in self.objects.items():
            candidates = obj.find_match_candidates(detected_objects_copy)
            # Some candidates were found for the object
            for c in candidates:
                match_canditates.append({'id': obj.id, 'mc_obj': c['mc_obj'], 'dist_sq': c['dist_sq']})
        
        match_canditates = sorted(match_canditates, key=lambda k: k['dist_sq'])
        while True:
            
            mc = None
            if not match_canditates:
                break
            else:
                mc = match_canditates[0]

            self.objects[mc['id']].update_state(mc['mc_obj'])
            try:
                detected_objects_copy.remove(mc['mc_obj'])
            except:
                pass
            match_canditates[:] = [m for m in match_canditates if not m['id'] == mc['id']]
            match_canditates[:] = [m for m in match_canditates if not m['mc_obj'] == mc['mc_obj']]

        for new_obj in detected_objects_copy:
            new_obj.id = Scene.get_id()
            self.objects[new_obj.id] = new_obj

        # Delete expired objects
        expired_list = []
        for i, obj in self.objects.items():
            if(obj.unseen > Scene.UNSEEN_ALLOWED):
                expired_list.append(i)

        for i in expired_list:    
            del self.objects[i]

        